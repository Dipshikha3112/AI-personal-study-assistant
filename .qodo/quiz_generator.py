import os
import re
import streamlit as st
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import pickle
import json
from datetime import datetime

os.environ["HF_TOKEN"] = "USE_YOUR_TOKEN"  # Replace with your actual token # removed for security


# Cache model loading to improve performance
@st.cache_resource
def load_models():
    """Load text generation and embedding models."""
    try:
        generator = pipeline("text-generation", model="t5-small", device=-1)
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Models loaded successfully: t5-small, all-MiniLM-L6-v2")
        return generator, embedding_model
    except Exception as e:
        print(f"Error loading models: {e}")
        return None, None

generator, embedding_model = load_models()

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

def web_search_questions(company, role, num_results=30):
    """Fetch interview questions from the web as a fallback."""
    query = f"{company} {role} interview questions 2025 site:*.edu | site:*.gov | site:glassdoor.com | site:interviewbit.com | site:tryexponent.com | site:geeksforgeeks.org"
    questions = set()
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        search_results = search(query, num_results=num_results)
        for result in search_results:
            try:
                response = requests.get(result, headers=headers, timeout=5)
                soup = BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    text = p.get_text().strip().lower()
                    if len(text) > 10 and any(keyword in text for keyword in ["write", "design", "tell me", "how would you", "explain"]):
                        questions.add(text[:200])  # Limit to 200 chars
            except Exception as e:
                print(f"Error fetching {result}: {e}")
        return questions
    except Exception as e:
        print(f"Web search error: {e}")
        return set()

def fetch_interview_questions(company, role, num_questions=50):
    """Fetch unique interview questions using FAISS, with web search and generation as fallbacks."""
    if faiss_index is None or not documents:
        print("FAISS index not available, falling back to web search")
        return list(web_search_questions(company, role, num_results=num_questions))[:num_questions]
    
    # Embed query
    try:
        query = f"{company} {role} interview questions 2025"
        query_embedding = embedding_model.encode([query], show_progress_bar=False)
        
        # Perform FAISS search
        distances, indices = faiss_index.search(np.array(query_embedding, dtype=np.float32), k=num_questions)
        similarities = [1 - (d / 2) for d in distances[0]]  # Convert L2 distance to cosine similarity
        questions = set()
        
        for idx, sim in zip(indices[0], similarities):
            if idx < len(documents) and sim >= 0.5:
                text = documents[idx].lower()
                if len(text) > 10 and any(keyword in text for keyword in ["write", "design", "tell me", "how would you", "explain"]):
                    questions.add(text[:200])
        
        # Fallback to web search if insufficient questions
        if len(questions) < num_questions:
            print(f"FAISS retrieved {len(questions)} questions, falling back to web search for {num_questions - len(questions)} more")
            web_questions = web_search_questions(company, role, num_results=num_questions - len(questions))
            questions.update(web_questions)
        
        # Generate additional questions if still short
        if len(questions) < num_questions and generator:
            num_needed = num_questions - len(questions)
            prompt = (
                f"Generate {num_needed} unique {company} {role} interview questions for 2025, "
                f"covering coding, system design, and behavioral topics. Format as a numbered list."
            )
            try:
                generated = generator(
                    prompt,
                    max_new_tokens=500,
                    num_return_sequences=1,
                    truncation=True
                )[0]["generated_text"]
                generated_questions = re.split(r'\d+\.\s+|[\n.?!]+', generated)
                for q in generated_questions:
                    q = q.strip()
                    if q and len(q) > 10 and len(questions) < num_questions:
                        questions.add(q[:200])
            except Exception as e:
                print(f"Error generating questions: {e}")
        
        return list(questions)[:num_questions]
    except Exception as e:
        print(f"Error in FAISS retrieval: {e}, falling back to web search")
        return list(web_search_questions(company, role, num_results=num_questions))[:num_questions]

def generate_quiz(company="Meta", role="Software Engineer", num_questions=10):
    """Generate a quiz with multiple-choice questions for interview preparation."""
    questions = fetch_interview_questions(company, role, num_questions)
    if not questions or any("error" in q.lower() for q in questions):
        # Fallback questions
        questions = [
            "Write a function to find the shortest path in a weighted graph.",
            "Design a scalable notification system for a social media platform.",
            "Describe a time you optimized a slow-performing application.",
            "Explain how you would implement a news feed ranking algorithm.",
            "Write code to detect a cycle in a directed graph."
        ] * 2  # Repeat to ensure enough questions
        questions = list(set(questions))[:num_questions]  # Deduplicate and limit
    
    quiz_data = []
    for idx, question in enumerate(questions, 1):
        # Embed question to retrieve context for options
        context = ""
        if faiss_index and documents:
            try:
                question_embedding = embedding_model.encode([question], show_progress_bar=False)
                distances, indices = faiss_index.search(np.array(question_embedding, dtype=np.float32), k=1)
                if indices[0][0] < len(documents) and (1 - distances[0][0] / 2) >= 0.5:
                    context = documents[indices[0][0]][:500]
            except Exception as e:
                print(f"Error retrieving context for question: {e}")
        
        # Fallback to web search for context if needed
        if not context:
            context = web_search_questions(f"{company} {role} {question}", num_results=1)
        
        prompt = (
            f"Generate a multiple-choice question for a {company} {role} interview based on: {question}. "
            f"Context: {context or 'None'}. Provide 4 options, one correct answer, and an explanation. "
            f"Format as: Question: ... Options: 1) ... 2) ... 3) ... 4) ... Correct Answer: ... Explanation: ..."
        )
        try:
            response = generator(
                prompt,
                max_new_tokens=300,
                num_return_sequences=1,
                truncation=True
            )[0]["generated_text"]
            
            # Parse response with regex for robustness
            question_text = ""
            options = []
            correct_answer = ""
            explanation = ""
            question_match = re.search(r"Question:.*?(?=\nOptions:|$)", response, re.DOTALL)
            options_match = re.search(r"Options:.*?(?=\nCorrect Answer:|$)", response, re.DOTALL)
            correct_match = re.search(r"Correct Answer:.*?(?=\nExplanation:|$)", response, re.DOTALL)
            explanation_match = re.search(r"Explanation:.*", response, re.DOTALL)
            
            if question_match:
                question_text = question_match.group(0).replace("Question:", "").strip()
            if options_match:
                options = [opt.strip() for opt in options_match.group(0).split("\n") if opt.strip().startswith(("1)", "2)", "3)", "4)"))]
            if correct_match:
                correct_answer = correct_match.group(0).replace("Correct Answer:", "").strip()
            if explanation_match:
                explanation = explanation_match.group(0).replace("Explanation:", "").strip()
            
            # Fallback for incomplete responses
            if len(options) < 4 or not correct_answer or not explanation:
                if "write" in question.lower() or "code" in question.lower():
                    options = [
                        "1) Use a depth-first search approach",
                        "2) Use a breadth-first search approach",
                        "3) Use a linear scan",
                        "4) Use a binary search"
                    ]
                    correct_answer = "1) Use a depth-first search approach"
                    explanation = f"For {company}, coding questions like this typically require efficient algorithms like DFS."
                elif "design" in question.lower():
                    options = [
                        "1) Use a monolithic architecture",
                        "2) Design a distributed system with sharding",
                        "3) Use a single database",
                        "4) Use a client-side cache"
                    ]
                    correct_answer = "2) Design a distributed system with sharding"
                    explanation = f"{company} system design questions focus on scalability."
                else:  # Behavioral
                    options = [
                        "1) Use the STAR method to structure your response",
                        "2) Provide a brief overview without details",
                        "3) Focus only on the outcome",
                        "4) Avoid mentioning challenges"
                    ]
                    correct_answer = "1) Use the STAR method to structure your response"
                    explanation = f"{company} values clear, structured behavioral responses."
            
            quiz_data.append({
                "question": question_text or question,
                "options": options[:4],  # Ensure exactly 4 options
                "correct_answer": correct_answer,
                "explanation": explanation
            })
        except Exception as e:
            print(f"Error generating quiz question for {question}: {e}")
            quiz_data.append({
                "question": question,
                "options": ["1) N/A", "2) N/A", "3) N/A", "4) N/A"],
                "correct_answer": "N/A",
                "explanation": f"Error generating question: {e}"
            })
    
    return quiz_data

def save_performance(company, role, score, total_questions):
    """Save performance data to JSON file."""
    performance_data = {
        "company": company,
        "role": role,
        "score": score,
        "total_questions": total_questions,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        os.makedirs("data", exist_ok=True)
        try:
            with open("data/performance_history.json", "r") as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []
        history.append(performance_data)
        with open("data/performance_history.json", "w") as f:
            json.dump(history, f, indent=4)
        print(f"Saved performance: {score}/{total_questions} for {company} {role}")
    except Exception as e:
        print(f"Error saving performance: {e}")

def load_performance():
    """Load performance history from JSON file."""
    try:
        with open("data/performance_history.json", "r") as f:
            history = json.load(f)
        return history
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading performance: {e}")
        return []

if __name__ == "__main__":
    # Example usage for testing
    quiz = generate_quiz("Meta", "Software Engineer", num_questions=5)
    for q in quiz:
        print(f"Question: {q['question']}")
        print("Options:", "\n".join(q['options']))
        print(f"Correct Answer: {q['correct_answer']}")
        print(f"Explanation: {q['explanation']}\n")
