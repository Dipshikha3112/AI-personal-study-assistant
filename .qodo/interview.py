import streamlit as st
import quiz_generator
from transformers import pipeline
import webbrowser
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def main():
    """Run the Streamlit mock interview interface."""
    st.set_page_config(page_title="Mock Interview", layout="wide")
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #ffffff, #f3e8ff);
        font-family: 'Segoe UI', sans-serif;
    }
    .question-container {
        background: #fff7ed;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        animation: fadeIn 0.5s;
    }
    .stButton>button {
        border-radius: 8px;
        background: #f97316;
        color: white;
        transition: background 0.3s;
    }
    .stButton>button:hover {
        background: #ea580c;
    }
    .stSelectbox {
        border-radius: 8px;
    }
    h1 {
        color: #4b0082;
        text-align: center;
    }
    .stRadio label {
        font-size: 16px;
    }
    .performance-container {
        background: #e5e7eb;
        border-radius: 10px;
        padding: 15px;
        margin-top: 20px;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Mock Interview for Engineering Roles")
    st.write("Select a company and role to start your mock interview.")

    # Initialize session state
    if "generator" not in st.session_state:
        st.session_state.generator = pipeline("text-generation", model="t5-small")
        st.session_state.model_name = "t5-small"
    if "quiz" not in st.session_state:
        st.session_state.quiz = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "quiz_completed" not in st.session_state:
        st.session_state.quiz_completed = False
    if "company" not in st.session_state:
        st.session_state.company = "Meta"
    if "role" not in st.session_state:
        st.session_state.role = "Software Engineer"

    # Company and role selection
    companies = sorted([
        "Amazon", "Apple", "Meta", "Google", "Microsoft", "Tesla", "Other"
    ])
    roles = [
        "Software Engineer", "Data Engineer", "Systems Engineer", "Machine Learning Engineer",
        "Embedded Systems Engineer", "Robotics Engineer", "Engineering Intern"
    ]
    col1, col2 = st.columns(2)
    with col1:
        company = st.selectbox("Select Company", companies, index=companies.index(st.session_state.company))
    with col2:
        role = st.selectbox("Select Role", roles, index=roles.index(st.session_state.role))
    if company == "Other":
        company = st.text_input("Enter Custom Company Name", value=st.session_state.company)

    if st.button("Generate Interview Questions"):
        with st.spinner(f"Fetching 50 unique {company} {role} interview questions..."):
            st.session_state.company = company
            st.session_state.role = role
            st.session_state.quiz = quiz_generator.generate_quiz(
                st.session_state.generator, st.session_state.model_name, company, role
            )
            st.session_state.current_page = 0
            st.session_state.answers = {}
            st.session_state.score = 0
            st.session_state.quiz_completed = False
        st.rerun()

    # Display performance history graph
    performance_data = quiz_generator.load_performance()
    filtered_data = [
        p for p in performance_data
        if p["company"] == st.session_state.company and p["role"] == st.session_state.role
    ]
    if filtered_data:
        st.subheader("Performance History")
        df = pd.DataFrame(filtered_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["percentage"] = (df["score"] / df["total_questions"]) * 100
        plt.figure(figsize=(6, 2))
        plt.bar(df["timestamp"].astype(str), df["percentage"], color=["#f97316", "#7e22ce"] * len(df))
        plt.title("Past Scores (%)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode()
        st.image(f"data:image/png;base64,{img_str}")
        plt.close()

    # Display quiz
    if st.session_state.quiz:
        questions_per_page = 10
        start_idx = st.session_state.current_page * questions_per_page
        end_idx = min(start_idx + questions_per_page, len(st.session_state.quiz))
        current_questions = st.session_state.quiz[start_idx:end_idx]

        st.subheader(f"Questions {start_idx + 1} - {end_idx} of {len(st.session_state.quiz)}")
        for i, q_data in enumerate(current_questions, start=start_idx):
            with st.container():
                st.markdown('<div class="question-container">', unsafe_allow_html=True)
                st.write(f"**Question {i + 1}:** {q_data['question']}")
                answer = st.radio(
                    f"Select answer for Question {i + 1}",
                    q_data["options"],
                    key=f"answer_{i}"
                )
                st.session_state.answers[i] = {
                    "selected": answer,
                    "correct": q_data["correct_answer"],
                    "explanation": q_data["explanation"]
                }
                st.markdown('</div>', unsafe_allow_html=True)

        # Pagination
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.current_page > 0:
                if st.button("Previous Page"):
                    st.session_state.current_page -= 1
                    st.rerun()
        with col3:
            if end_idx < len(st.session_state.quiz):
                if st.button("Next Page"):
                    st.session_state.current_page += 1
                    st.rerun()

        if st.button("Submit Answers"):
            for i in range(len(st.session_state.quiz)):
                answer_data = st.session_state.answers.get(i, {})
                if answer_data.get("selected") == answer_data.get("correct"):
                    st.session_state.score += 1
            quiz_generator.save_performance(
                st.session_state.company, st.session_state.role,
                st.session_state.score, len(st.session_state.quiz)
            )
            st.session_state.quiz_completed = True
            st.rerun()

    # Display results
    if st.session_state.quiz_completed:
        st.subheader("Quiz Results")
        st.write(f"**Score: {st.session_state.score}/{len(st.session_state.quiz)} ({st.session_state.score / len(st.session_state.quiz) * 100:.2f}%)**")
        for i, answer_data in st.session_state.answers.items():
            st.write(f"**Question {i + 1}:** {st.session_state.quiz[i]['question']}")
            st.write(f"**Your Answer:** {answer_data['selected']}")
            st.write(f"**Correct Answer:** {answer_data['correct']}")
            st.write(f"**Explanation:** {answer_data['explanation']}")
            st.markdown("---")

        if st.button("Restart Interview"):
            st.session_state.quiz = []
            st.session_state.current_page = 0
            st.session_state.answers = {}
            st.session_state.score = 0
            st.session_state.quiz_completed = False
            st.rerun()

if __name__ == "__main__":
    main()