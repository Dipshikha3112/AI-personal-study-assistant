import streamlit as st
import study_assistant
import chat_history
import quiz_generator
import time
import re
import os
import webbrowser

def parse_quiz(quiz_text):
    """Parse quiz text into structured questions, options, and answers."""
    questions = []
    lines = quiz_text.split("\n")
    current_question = None
    current_options = []
    current_answer = None
    current_tip = None
    for line in lines:
        line = line.strip()
        if line.startswith("Question:"):
            if current_question:
                questions.append((current_question, current_options, current_answer, current_tip))
            current_question = line.replace("Question:", "").strip()
            current_options = []
            current_answer = None
            current_tip = None
        elif line.startswith(("1)", "2)", "3)", "4)")):
            current_options.append(line)
        elif line.startswith("Correct Answer:"):
            current_answer = line.replace("Correct Answer:", "").strip()
        elif line.startswith("Tip:"):
            current_tip = line.replace("Tip:", "").strip()
    if current_question:
        questions.append((current_question, current_options, current_answer, current_tip))
    return questions

def main():
    """Run the Streamlit web app for the study assistant chatbot."""
    st.title("📚 Personal Study Assistant")
    st.write("Ask questions, set goals, generate quizzes, or prepare for interviews!")

    # Initialize session state
    if "model_name" not in st.session_state:
        st.session_state.model_name = "t5-small"  # Default model
        st.session_state.chat_history = chat_history.load_chat_history()
        st.session_state.awaiting_feedback = False
        st.session_state.last_input = None
        st.session_state.last_answer = None
        st.session_state.debug_response = ""
        st.session_state.current_input_type = "Question"
        st.session_state.pomodoro_running = False
        st.session_state.pomodoro_time = 25 * 60
        st.session_state.quiz_answers = {}
        st.session_state.current_quiz = None
        st.session_state.quiz_submitted = False

    # Sidebar for model selection, history, and productivity tools
    with st.sidebar:
        st.header("Model Settings")
        model_name = st.selectbox(
            "Select Model",
            ["gpt2", "t5-small", "facebook/bart-large"],
            index=1 if st.session_state.model_name == "t5-small" else 0 if st.session_state.model_name == "gpt2" else 2
        )
        if model_name != st.session_state.model_name:
            with st.spinner("Loading model..."):
                st.session_state.model_name = model_name
                st.session_state.chat_history = []  # Clear history on model change
                chat_history.save_chat_history(st.session_state.chat_history)

        st.header("Chat History")
        if st.session_state.chat_history:
            for i, (speaker, message) in enumerate(st.session_state.chat_history):
                with st.expander(f"{speaker} ({i+1})"):
                    st.write(message)
        if st.button("Clear History"):
            chat_history.clear_chat_history()
            st.session_state.chat_history = []
            st.rerun()

        st.header("Pomodoro Timer")
        pomodoro_duration = st.slider("Pomodoro Duration (minutes)", 5, 60, 25)
        if st.button("Start Pomodoro"):
            st.session_state.pomodoro_running = True
            st.session_state.pomodoro_time = pomodoro_duration * 60
        if st.button("Stop Pomodoro"):
            st.session_state.pomodoro_running = False
        if st.session_state.pomodoro_running:
            st.markdown('<div class="timer-container">', unsafe_allow_html=True)
            st.write(f"Time Left: {st.session_state.pomodoro_time // 60}:{st.session_state.pomodoro_time % 60:02d}")
            st.markdown('</div>', unsafe_allow_html=True)
            time.sleep(1)
            st.session_state.pomodoro_time -= 1
            if st.session_state.pomodoro_time <= 0:
                st.session_state.pomodoro_running = False
                st.success("Pomodoro session complete!")
            st.rerun()

        st.header("Reminders")
        reminder_text = st.text_input("Set Reminder", placeholder="e.g., Study algorithms at 7 PM")
        if st.button("Add Reminder"):
            if reminder_text.strip():
                st.session_state.chat_history.append(("Reminder", reminder_text))
                chat_history.save_chat_history(st.session_state.chat_history)
                st.success("Reminder added!")
                st.rerun()

        st.header("Mock Interview")
        if st.button("Attempt Your Mock Interview Now"):
            interview_script = os.path.join(os.path.dirname(__file__), "interview.py")
            port = 8502
            cmd = f"streamlit run {interview_script} --server.port {port}"
            os.system(cmd)
            webbrowser.open(f"http://localhost:{port}")
            st.session_state.chat_history.append(("Assistant", f"Started {st.session_state.get('company', 'Mock')} {st.session_state.get('role', 'Interview')} Mock Interview in a new window."))
            chat_history.save_chat_history(st.session_state.chat_history)
            st.rerun()

    # Input section
    st.subheader("Ask a Question, Set a Goal, or Prepare for an Interview")
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input("Enter a question, goal, or interview prep topic", placeholder="e.g., What is the Pythagorean theorem? or Learn Python in 30 days or Interview questions for Google")
    with col2:
        input_type = st.selectbox("Input Type", ["Question", "Goal", "Interview Prep"], key="input_type_select")

    if st.button("Submit"):
        # Handle empty or vague input
        if not user_input.strip():
            user_input = "Provide a general answer or information relevant to software engineering."
        
        with st.spinner("Processing..."):
            st.session_state.chat_history.append(("You", user_input))
            st.session_state.current_input_type = input_type
            st.session_state.quiz_submitted = False
            if input_type == "Question":
                response = study_assistant.generate_response(user_input, st.session_state.model_name)
                st.session_state.chat_history.append(("Assistant", response))
                st.session_state.debug_response = response
            elif input_type == "Goal":
                response = study_assistant.generate_study_plan(user_input, st.session_state.model_name)
                st.session_state.chat_history.append(("Assistant (Study Plan)", response))
                st.session_state.debug_response = response
            else:  # Interview Prep
                company = None
                if "for" in user_input.lower():
                    company = user_input.lower().split("for")[-1].strip()
                response = study_assistant.generate_quiz(
                    topic=user_input,
                    model_name=st.session_state.model_name,
                    is_interview_prep=True,
                    company=company
                )
                response_text = "\n".join([
                    f"Question: {q[0]}\n" + "\n".join(q[1]) + f"\nCorrect Answer: {q[2]}\nTip: {q[3] if q[3] else 'No tip provided'}\n"
                    for q in parse_quiz(response)
                ])
                st.session_state.chat_history.append(("Assistant (Quiz)", response_text))
                st.session_state.current_quiz = response_text
                st.session_state.quiz_answers = {}
                st.session_state.debug_response = response
            st.session_state.awaiting_feedback = True
            st.session_state.last_input = user_input
            st.session_state.last_answer = response
            chat_history.save_chat_history(st.session_state.chat_history)
            st.rerun()

    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for speaker, message in st.session_state.chat_history:
        if speaker == "You":
            st.markdown(f'<div class="chat-message user-message">{message}</div>', unsafe_allow_html=True)
        elif speaker == "Assistant (after web search)":
            st.markdown(f'<div class="chat-message assistant-web-message">{message}</div>', unsafe_allow_html=True)
        elif speaker == "Assistant (Study Plan)":
            st.markdown(f'<div class="chat-message assistant-plan-message">{message}</div>', unsafe_allow_html=True)
        elif speaker == "Assistant (Quiz)":
            st.markdown(f'<div class="chat-message assistant-quiz-message">{message}</div>', unsafe_allow_html=True)
        elif speaker == "Reminder":
            st.markdown(f'<div class="chat-message assistant-message">Reminder: {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message">{message}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Interactive quiz answering
    if st.session_state.current_quiz and st.session_state.current_input_type == "Interview Prep" and not st.session_state.quiz_submitted:
        st.subheader("Quiz")
        questions = parse_quiz(st.session_state.current_quiz)
        for i, (question, options, correct_answer, tip) in enumerate(questions):
            with st.container():
                st.markdown(f'<div class="quiz-input">', unsafe_allow_html=True)
                st.write(f"**Question {i+1}:** {question}")
                answer = st.radio(f"Select answer for Question {i+1}", options, key=f"quiz_{i}")
                st.session_state.quiz_answers[i] = {"selected": answer, "correct": correct_answer, "tip": tip}
                st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Submit All Answers"):
            st.session_state.quiz_submitted = True
            score = 0
            for i, answer_data in st.session_state.quiz_answers.items():
                selected = answer_data["selected"]
                correct = answer_data["correct"]
                tip = answer_data["tip"]
                if selected == correct:
                    score += 1
                    st.success(f"Question {i+1}: Correct!")
                else:
                    st.error(f"Question {i+1}: Incorrect. Correct answer: {correct}")
                    if tip:
                        st.info(f"Tip: {tip}")
            st.write(f"**Score: {score}/{len(questions)}**")
            quiz_generator.save_performance(
                company="Mock" if "company" not in st.session_state else st.session_state.company,
                role="Software Engineer",
                score=score,
                total_questions=len(questions)
            )
            st.session_state.chat_history.append(("Assistant (Quiz Results)", f"Score: {score}/{len(questions)}"))
            chat_history.save_chat_history(st.session_state.chat_history)
            st.rerun()

    # Feedback mechanism
    if st.session_state.awaiting_feedback and st.session_state.chat_history and not st.session_state.quiz_submitted:
        st.write("Was this answer okay?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes"):
                st.session_state.awaiting_feedback = False
                st.success("Thank you for your feedback!")
                chat_history.save_chat_history(st.session_state.chat_history)
                st.rerun()
        with col2:
            if st.button("No"):
                with st.spinner("Generating a better response..."):
                    if st.session_state.current_input_type == "Question":
                        response = study_assistant.generate_response(st.session_state.last_input, st.session_state.model_name)
                        st.session_state.chat_history.append(("Assistant (after feedback)", response))
                    elif st.session_state.current_input_type == "Goal":
                        response = study_assistant.generate_study_plan(st.session_state.last_input, st.session_state.model_name)
                        st.session_state.chat_history.append(("Assistant (Study Plan after feedback)", response))
                    else:  # Interview Prep
                        company = None
                        if "for" in st.session_state.last_input.lower():
                            company = st.session_state.last_input.lower().split("for")[-1].strip()
                        response = study_assistant.generate_quiz(
                            topic=st.session_state.last_input,
                            model_name=st.session_state.model_name,
                            is_interview_prep=True,
                            company=company
                        )
                        response_text = "\n".join([
                            f"Question: {q[0]}\n" + "\n".join(q[1]) + f"\nCorrect Answer: {q[2]}\nTip: {q[3] if q[3] else 'No tip provided'}\n"
                            for q in parse_quiz(response)
                        ])
                        st.session_state.chat_history.append(("Assistant (Quiz after feedback)", response_text))
                        st.session_state.current_quiz = response_text
                        st.session_state.quiz_answers = {}
                    st.session_state.last_answer = response
                    st.session_state.debug_response = response
                    chat_history.save_chat_history(st.session_state.chat_history)
                    st.rerun()

    # Debug info
    with st.expander("Debug Info"):
        st.write(f"Raw response: {st.session_state.debug_response}")

if __name__ == "__main__":
    main()
