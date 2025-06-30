import os
import re
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Set Hugging Face token (optional for these models)
os.environ["HF_TOKEN"] = "Your-token-here"  # Replace with your actual token

def load_model(model_name="gpt2"):
    """Load the language model and tokenizer based on the selected model."""
    try:
        if model_name == "t5-small":
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer, device=-1)
        elif model_name == "gpt2":
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        elif model_name == "facebook/bart-large":
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        print(f"Loaded model: {model_name}")
        return generator, model_name
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, model_name

def web_search(query, num_results=3):
    """Perform a free web search using googlesearch-python and extract content."""
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
                    results.append(text[:500])
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        return " ".join(results) if results else "No relevant web results found."
    except Exception as e:
        return f"Web search error: {e}"

def generate_response(generator, user_input, model_name, max_tokens=150, web_context=None):
    """Generate a response from the model, optionally using web context."""
    if model_name == "t5-small":
        prompt = f"question: {user_input} context: You are a study assistant. Provide a clear, concise, and accurate answer. Use mathematical notation if needed. Web context: {web_context or 'None'} answer: "
    else:
        prompt = (
            f"You are a study assistant specializing in accurate, concise academic answers. "
            f"Answer only the question asked in clear language, using mathematical notation if needed. "
            f"Do not repeat the question, generate new questions, or include unrelated content. "
            f"If the question is unclear, say so. Web context: {web_context or 'None'}\nQuestion: {user_input}\nAnswer: "
        )
    try:
        if model_name == "t5-small":
            response = generator(
                prompt,
                max_length=max_tokens,
                num_return_sequences=1,
                truncation=True
            )[0]["generated_text"]
            answer = response.strip()
        else:
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
        if "theorem" in user_input.lower() or "math" in user_input.lower():
            if not any(term in answer.lower() for term in ["equation", "a^2", "b^2", "c^2", "square", "triangle"]):
                return "I couldn't provide an accurate mathematical answer. Please try rephrasing or ask another question."
        return answer
    except Exception as e:
        return f"Error generating response: {e}"

def generate_study_plan(generator, goal, model_name, max_tokens=300, web_context=None):
    """Generate a study plan based on the user's learning goal."""
    if model_name == "t5-small":
        prompt = f"task: Create a study plan for the goal: {goal}. Provide a concise, structured plan with steps and a timeline. answer: "
    else:
        prompt = (
            f"You are a study assistant tasked with creating a structured study plan for the goal: {goal}. "
            f"Provide a concise plan with clear steps, a timeline, and specific tasks. "
            f"Do not include unrelated content or questions. Format as a numbered list. Web context: {web_context or 'None'}\nGoal: {goal}\nStudy Plan: "
        )
    try:
        if model_name == "t5-small":
            response = generator(
                prompt,
                max_length=max_tokens,
                num_return_sequences=1,
                truncation=True
            )[0]["generated_text"]
            plan = response.strip()
        else:
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
    except Exception as e:
        return f"Error generating study plan: {e}"

def generate_quiz(generator, topic, model_name, is_interview_prep=False, company=None, max_tokens=300, web_context=None):
    """Generate a quiz with questions, options, and answers for a topic or interview prep."""
    if is_interview_prep:
        prompt = (
            f"You are a study assistant creating a quiz for interview preparation for a software developer role at {company or 'a tech company'}. "
            f"Generate a quiz with 3 questions (mix of coding, behavioral, and HR-related), each with 4 multiple-choice options and the correct answer. "
            f"Include tips for answering and use web context if provided. Format as: Question: ... Options: 1) ... 2) ... 3) ... 4) ... Correct Answer: ... Tip: ... "
            f"Web context: {web_context or 'None'}\nQuiz: "
        )
    else:
        prompt = (
            f"You are a study assistant creating a quiz on the topic: {topic}. "
            f"Generate a quiz with 3 questions, each with 4 multiple-choice options and the correct answer. "
            f"Focus on academic or study-related content. Format as: Question: ... Options: 1) ... 2) ... 3) ... 4) ... Correct Answer: ... "
            f"Web context: {web_context or 'None'}\nQuiz: "
        )
    try:
        if model_name == "t5-small":
            response = generator(
                prompt,
                max_length=max_tokens,
                num_return_sequences=1,
                truncation=True
            )[0]["generated_text"]
            quiz = response.strip()
        else:
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
    except Exception as e:
        return f"Error generating quiz: {e}"

def main():
    """Console-based interface (not used in web app)."""
    print("This script is designed to be called by app.py. Run 'streamlit run app.py' instead.")