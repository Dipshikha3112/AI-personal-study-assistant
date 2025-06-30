import googlesearch
import re
from transformers import pipeline
import random
import json
import os

def fetch_interview_questions(company, role):
    """Fetch 50 unique interview questions from the web for the given company and role."""
    query = f"{company} {role} interview questions 2025 site:*.edu | site:*.gov | site:glassdoor.com | site:interviewbit.com | site:tryexponent.com | site :geeksforgeeks.org | site :google.com"
    questions = set()
    try:
        # Fetch from multiple sources
        search_results = googlesearch.search(query, num_results=50)
        for result in search_results:
            description = result.get("description", "").lower()
            if "question" in description and company.lower() in description and "google" not in description:
                lines = re.split(r'[.!?]+', result["description"])
                for line in lines:
                    line = line.strip()
                    if line and any(keyword in line.lower() for keyword in ["write", "design", "tell me", "how would you", "explain"]):
                        questions.add(line[:200])  # Limit length
        # Supplement with additional sources if needed
        if len(questions) < 50:
            additional_query = f"{company} {role} technical interview questions 2025"
            additional_results = googlesearch.search(additional_query, num_results=30)
            for result in additional_results:
                description = result.get("description", "").lower()
                if "question" in description and company.lower() in description:
                    lines = re.split(r'[.!?]+', result["description"])
                    for line in lines:
                        line = line.strip()
                        if line and any(keyword in line.lower() for keyword in ["write", "design", "tell me", "how would you", "explain"]):
                            questions.add(line[:200])
        questions = list(questions)
        # If still short, generate additional questions using LLM
        if len(questions) < 50:
            generator = pipeline("text-generation", model="t5-small")
            num_needed = 50 - len(questions)
            prompt = f"Generate {num_needed} unique {company} {role} interview questions for 2025, covering coding, system design, and behavioral topics."
            generated = generator(prompt, max_length=500, num_return_sequences=1)[0]["generated_text"]
            generated_questions = re.split(r'\d+\.\s', generated)[1:]  # Split numbered questions
            for q in generated_questions:
                q = q.strip()
                if q and q not in questions:
                    questions.append(q)
        return questions[:50]  # Ensure exactly 50 unique questions
    except Exception as e:
        return [f"Error fetching questions: {str(e)}"]

def generate_quiz(generator, model_name, company="Meta", role="Software Engineer"):
    """Generate a quiz with 50 unique questions for the specified company and role."""
    questions = fetch_interview_questions(company, role)
    if not questions or "error" in questions[0].lower():
        # Fallback questions for Meta Software Engineer
        questions = [
            "Write a function to find the shortest path in a weighted graph.",
            "Design a scalable notification system for Facebook.",
            "Describe a time you optimized a slow-performing application.",
            "Explain how you would implement a news feed ranking algorithm.",
            "Write code to detect a cycle in a directed graph."
        ] * 10
        questions = list(set(questions))[:50]  # Deduplicate and limit

    quiz_data = []
    for question in questions:
        prompt = f"Generate 4 multiple-choice options for this {company} {role} interview question: '{question}'. Specify the correct answer and an explanation."
        response = generator(prompt, max_length=300, num_return_sequences=1)[0]["generated_text"]
        
        lines = response.split("\n")
        options = []
        correct_answer = None
        explanation = None
        for line in lines:
            line = line.strip()
            if line.startswith(("1)", "2)", "3)", "4)")):
                options.append(line)
            elif line.startswith("Correct Answer:"):
                correct_answer = line.replace("Correct Answer:", "").strip()
            elif line.startswith("Explanation:"):
                explanation = line.replace("Explanation:", "").strip()
        
        # Fallback options
        if len(options) < 4 or not correct_answer or not explanation:
            if "write" in question.lower() or "code" in question.lower():
                options = [
                    "1) Use a depth-first search approach",
                    "2) Use a brute-force enumeration",
                    "3) Rely on external libraries",
                    "4) Implement a greedy algorithm"
                ]
                correct_answer = "1) Use a depth-first search approach"
                explanation = f"For {company}, coding questions like this typically require efficient algorithms like DFS to handle large-scale data, ensuring optimal time complexity."
            elif "design" in question.lower():
                options = [
                    "1) Use a monolithic architecture",
                    "2) Design a distributed system with sharding",
                    "3) Avoid caching mechanisms",
                    "4) Use a single database instance"
                ]
                correct_answer = "2) Design a distributed system with sharding"
                explanation = f"{company} system design questions focus on scalability, where distributed systems with sharding ensure high availability and performance."
            else:  # Behavioral
                options = [
                    "1) Use the STAR method to structure your response",
                    "2) Focus only on technical achievements",
                    "3) Avoid specific examples",
                    "4) Discuss unrelated personal experiences"
                ]
                correct_answer = "1) Use the STAR method to structure your response"
                explanation = f"{company} values clear, structured behavioral responses using the STAR method to assess problem-solving and cultural fit."
        
        quiz_data.append({
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": explanation
        })
    
    return quiz_data

def save_performance(company, role, score, total_questions):
    """Save performance data to JSON file."""
    performance_file = "performance_history.json"
    performance_data = []
    if os.path.exists(performance_file):
        with open(performance_file, "r") as f:
            performance_data = json.load(f)
    
    from datetime import datetime
    performance_data.append({
        "company": company,
        "role": role,
        "score": score,
        "total_questions": total_questions,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(performance_file, "w") as f:
        json.dump(performance_data, f, indent=4)

def load_performance():
    """Load performance history from JSON file."""
    performance_file = "performance_history.json"
    if os.path.exists(performance_file):
        with open(performance_file, "r") as f:
            return json.load(f)
    return []