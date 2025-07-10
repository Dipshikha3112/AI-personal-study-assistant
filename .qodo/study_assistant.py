import os
import re
import streamlit as st
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import pickle
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Placeholder for Hugging Face token (not used as models are public)
os.environ["HF_TOKEN"] = "USE_YOUR_TOKEN"  # Replace with your actual token # removed for security


# Cache embedding model loading for FAISS
@st.cache_resource
def load_embedding_model():
    """Load embedding model for FAISS."""
    try:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded: all-MiniLM-L6-v2")
        return embedding_model
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        return None

embedding_model = load_embedding_model()

# Cache FAISS index loading
@st.cache_resource
def load_faiss_index(index_path="data/faiss_index", docs_path="data/documents.pkl"):
    """Load FAISS index and documents from disk."""
    try:
        index = faiss.read_index(index_path)
        with open(docs_path, "rb") as f:
            documents = pickle.load(f)
        print(f"Loaded FAISS index with {len(documents)} documents")
        return index, documents
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None, []

faiss_index, documents = load_faiss_index()

# Cache model loading based on model_name
@st.cache_resource
def load_model(model_name):
    """Load a single text generation model based on model_name."""
    try:
        if model_name == "t5-small":
            tokenizer = AutoTokenizer.from_pretrained("t5-small")
            model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")
            generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer, device=-1)
        elif model_name == "facebook/bart-large":
            tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large")
            model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large")
            generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        else:  # Default to gpt2
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
            model = AutoModelForCausalLM.from_pretrained("gpt2")
            generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        print(f"Model loaded successfully: {model_name}")
        return generator, None  # Return tuple for compatibility with app.py
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        return None, None

def web_search(query, num_results=3):
    """Perform a web search as a fallback if FAISS retrieval is insufficient."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        results = []
        for url in search(query, num_results=num_results):
            try:
                response = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("p")
                text = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                if text:
                    results.append(text[:500])  # Limit to 500 chars per result
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        return " ".join(results) if results else "No relevant web results found."
    except Exception as e:
        return f"Web search error: {e}"

def retrieve_context(query, k=3, similarity_threshold=0.5):
    """Retrieve context using FAISS, with web search as fallback."""
    if faiss_index is None or not documents or embedding_model is None:
        print("FAISS index or embedding model not available, falling back to web search")
        return web_search(query, num_results=k)
    
    # Embed query
    try:
        query_embedding = embedding_model.encode([query], show_progress_bar=False)
        
        # Perform FAISS search
        distances, indices = faiss_index.search(np.array(query_embedding, dtype=np.float32), k)
        similarities = [1 - (d / 2) for d in distances[0]]  # Convert L2 distance to cosine similarity
        context = []
        
        for idx, sim in zip(indices[0], similarities):
            if idx < len(documents) and sim >= similarity_threshold:
                context.append(documents[idx][:500])  # Limit to 500 chars per document
        
        # Fallback to web search if insufficient results
        if len(context) < k:
            print(f"FAISS retrieved {len(context)} results, falling back to web search for {k - len(context)} more")
            web_context = web_search(query, num_results=k - len(context))
            context.append(web_context)
        
        return " ".join(context) if context else "No relevant context found."
    except Exception as e:
        print(f"Error in FAISS retrieval: {e}, falling back to web search")
        return web_search(query, num_results=k)

def generate_response(query, model_name="gpt2", max_tokens=150):
    """Generate a response using the selected model and retrieved context."""
    generator, _ = load_model(model_name)
    if generator is None:
        return "Error loading model. Please try another model or check dependencies."
    
    context = retrieve_context(query)
    if model_name == "t5-small":
        prompt = (
            f"question: {query} context: You are a study assistant. Provide a clear, concise, and accurate answer. "
            f"Use mathematical notation if needed. Web context: {context or 'None'} answer: "
        )
        response = generator(
            prompt,
            max_new_tokens=max_tokens,
            num_return_sequences=1,
            truncation=True
        )[0]["generated_text"]
        answer = response.strip()
    else:  # gpt2 or facebook/bart-large
        prompt = (
            f"You are a study assistant specializing in accurate, concise academic answers. "
            f"Answer only the question asked in clear language, using mathematical notation if needed. "
            f"Do not repeat the question, generate new questions, or include unrelated content. "
            f"If the question is unclear, say so. Web context: {context or 'None'}\nQuestion: {query}\nAnswer: "
        )
        response = generator(
            prompt,
            max_new_tokens=max_tokens,
            num_return_sequences=1,
            truncation=True,
            pad_token_id=generator.tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.9,
            temperature=0.6
        )[0]["generated_text"]
        answer = response[len(prompt):].strip()
        answer = re.sub(r"[_]+|Question:.*|Answer:.*|provide.*study assistant.*", "", answer, flags=re.IGNORECASE).strip()
    
    print(f"[DEBUG] Raw response: {response}")
    if not answer or len(answer) < 10 or "study assistant" in answer.lower():
        return "I couldn't generate a clear answer. Please try rephrasing your question."
    if "theorem" in query.lower() or "math" in query.lower():
        if not any(term in answer.lower() for term in ["equation", "a^2", "b^2", "c^2", "square", "triangle"]):
            return "I couldn't provide an accurate mathematical answer. Please try rephrasing or ask another question."
    return answer

def generate_study_plan(goal, model_name="gpt2", max_tokens=300):
    """Generate a study plan based on the user's learning goal."""
    generator, _ = load_model(model_name)
    if generator is None:
        return "Error loading model. Please try another model or check dependencies."
    
    context = retrieve_context(f"{goal} study plan")
    if model_name == "t5-small":
        prompt = (
            f"task: Create a study plan for the goal: {goal}. Provide a concise, structured plan with steps and a timeline. "
            f"Web context: {context or 'None'} answer: "
        )
        response = generator(
            prompt,
            max_new_tokens=max_tokens,
            num_return_sequences=1,
            truncation=True
        )[0]["generated_text"]
        plan = response.strip()
    else:
        prompt = (
            f"You are a study assistant tasked with creating a structured study plan for the goal: {goal}. "
            f"Provide a concise plan with clear steps, a timeline, and specific tasks. "
            f"Do not include unrelated content or questions. Format as a numbered list. Web context: {context or 'None'}\nGoal: {goal}\nStudy Plan: "
        )
        response = generator(
            prompt,
            max_new_tokens=max_tokens,
            num_return_sequences=1,
            truncation=True,
            pad_token_id=generator.tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.9,
            temperature=0.7
        )[0]["generated_text"]
        plan = response[len(prompt):].strip()
        plan = re.sub(r"[_]+|Goal:.*|Study Plan:.*", "", plan, flags=re.IGNORECASE).strip()
    
    print(f"[DEBUG] Raw study plan response: {response}")
    if not plan or len(plan) < 10:
        return "I couldn't generate a clear study plan. Please try rephrasing your goal."
    return plan

def generate_quiz(topic, model_name="gpt2", is_interview_prep=False, company=None, max_tokens=300):
    """Generate a quiz with questions, options, and answers for a topic or interview prep."""
    generator, _ = load_model(model_name)
    if generator is None:
        return "Error loading model. Please try another model or check dependencies."
    
    context = retrieve_context(f"{topic} quiz questions" if not is_interview_prep else f"{company} {topic} interview questions 2025")
    if model_name == "t5-small":
        prompt = (
            f"task: Create a quiz for {'interview preparation for a software developer role at ' + (company or 'a tech company') if is_interview_prep else f'the topic: {topic}'}. "
            f"Generate a quiz with 3 questions, each with 4 multiple-choice options and the correct answer. "
            f"{'Include tips for answering.' if is_interview_prep else 'Focus on academic content.'} "
            f"Format as: Question: ... Options: 1) ... 2) ... 3) ... 4) ... Correct Answer: ... {'Tip: ...' if is_interview_prep else ''} "
            f"Web context: {context or 'None'} answer: "
        )
        response = generator(
            prompt,
            max_new_tokens=max_tokens,
            num_return_sequences=1,
            truncation=True
        )[0]["generated_text"]
        quiz = response.strip()
    else:
        prompt = (
            f"You are a study assistant creating a quiz for {'interview preparation for a software developer role at ' + (company or 'a tech company') if is_interview_prep else f'the topic: {topic}'}. "
            f"Generate a quiz with 3 questions, each with 4 multiple-choice options and the correct answer. "
            f"{'Include a mix of coding, behavioral, and HR-related questions. Include tips for answering.' if is_interview_prep else 'Focus on academic or study-related content.'} "
            f"Format as: Question: ... Options: 1) ... 2) ... 3) ... 4) ... Correct Answer: ... {'Tip: ...' if is_interview_prep else ''} "
            f"Web context: {context or 'None'}\nQuiz: "
        )
        response = generator(
            prompt,
            max_new_tokens=max_tokens,
            num_return_sequences=1,
            truncation=True,
            pad_token_id=generator.tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.9,
            temperature=0.7
        )[0]["generated_text"]
        quiz = response[len(prompt):].strip()
        quiz = re.sub(r"[_]+|Quiz:.*", "", quiz, flags=re.IGNORECASE).strip()
    
    print(f"[DEBUG] Raw quiz response: {response}")
    if not quiz or len(quiz) < 10:
        return "I couldn't generate a clear quiz. Please try rephrasing your topic or company."
    return quiz

def main():
    """Console-based interface (not used in web app)."""
    print("This script is designed to be called by app.py. Run 'streamlit run app.py' instead.")

if __name__ == "__main__":
    main()
