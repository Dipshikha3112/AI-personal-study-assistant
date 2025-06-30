AI Personal Study Coach
Overview
The AI Personal Study Coach is a Streamlit-based web application designed to assist students, particularly those preparing for technical interviews, by providing a chatbot for answering questions, generating study plans, and creating realistic mock interview quizzes. This project was developed as an exciting learning endeavor to deepen my understanding of Python, web development, and AI, as I'm new to programming and eager to build practical, interactive tools.
The application consists of two main interfaces:

Chatbot Interface (app.py): A versatile assistant that answers questions, creates study plans, generates quizzes, and supports productivity tools like a Pomodoro timer and reminders.
Mock Interview Interface (interview.py): A dedicated interface for simulating technical interviews with 50 unique, company-specific questions, performance tracking, and visual feedback.

Features

Chatbot Interface:

Question Answering: Answers any query (e.g., "What is the Pythagorean theorem?") using web searches and LLMs (t5-small by default) on the first attempt, even for vague inputs.
Study Plans: Generates structured learning plans (e.g., "Learn Python in 30 days") with daily tasks.
Interview Prep Quizzes: Creates short quizzes (3 questions) for interview preparation, with multiple-choice options and feedback.
Productivity Tools: Includes a Pomodoro timer and reminder system to boost study efficiency.
Chat History: Saves interactions in chat_history.json for review.
Modern Design: Uses a white/orange/purple theme with fade-in animations for a user-friendly experience.


Mock Interview Interface:

Company and Role Selection: Choose from a sorted list of companies (e.g., Meta, Google) and roles (e.g., Software Engineer, Data Engineer) suitable for all engineering branches.
50 Unique Questions: Fetches 50 distinct questions via web search (e.g., Glassdoor, InterviewBit) tailored to the selected company and role, displayed 10 per page with pagination.
Performance Tracking: Saves scores in performance_history.json and displays a colorful mini-graph (orange/purple) of past scores at the start of each attempt.
Results Display: Shows only questions, selected answers, correct answers, and LLM-generated explanations post-submission.
Realistic Questions: Covers coding (e.g., graph algorithms), system design (e.g., notification systems), and behavioral questions (e.g., STAR method), specific to the company.


Concurrency: Both interfaces run simultaneously (app.py on port 8501, interview.py on port 8502).


Project Motivation
As a beginner in programming, I started this project to explore Python, Streamlit, and AI tools like Transformers, while building something practical and engaging. By creating an interactive study assistant with real-world applications like interview preparation, I aimed to strengthen my skills in web development, API integration, and data handling. This project combines my interest in AI and education, making learning both fun and effective.
Project Structure
C:\Users\emeli\Music\AI Personal Study Coach\.qodo\
├── app.py                  # Main chatbot interface
├── interview.py            # Mock interview interface
├── quiz_generator.py       # Generates 50 unique interview questions
├── study_assistant.py      # Handles LLM and web search logic
├── chat_history.py         # Manages chat history storage
├── chat_history.json       # Stores chatbot interactions
├── performance_history.json # Stores mock interview performance
└── README.md               # Project documentation

File Descriptions

app.py: The main Streamlit app for the chatbot, handling question answering, study plans, quizzes, Pomodoro timer, reminders, and chat history. It triggers the mock interview via a sidebar button.
interview.py: A separate Streamlit app for mock interviews, with dropdowns for company/role, 50 unique questions, pagination, and performance tracking with a mini-graph.
quiz_generator.py: Fetches 50 unique questions from web searches (e.g., Glassdoor, InterviewBit) using googlesearch-python, generates multiple-choice options and explanations with t5-small, and saves performance data.
study_assistant.py: Contains LLM logic (t5-small, gpt2, or facebook/bart-large) and web search integration for the chatbot.
chat_history.py: Manages saving/loading chat history to/from chat_history.json.

Setup Instructions

Clone the Repository (or manually create files):

Place all files in C:\Users\emeli\Music\AI Personal Study Coach\.qodo\.


Install Dependencies:
pip install streamlit transformers googlesearch-python pandas matplotlib


Run the Chatbot:
cd C:\Users\emeli\Music\AI Personal Study Coach\.qodo
streamlit run app.py


Opens at http://localhost:8501.


Run the Mock Interview (optional, auto-triggered from app.py):
streamlit run interview.py --server.port 8502


Opens at http://localhost:8502.



Usage
Chatbot Interface (http://localhost:8501)

Select Model: Choose t5-small (recommended) from the sidebar for better accuracy.
Input Query:
Question: E.g., "What is the Pythagorean theorem?" or "Tell me something" (web search on first attempt).
Goal: E.g., "Learn Python in 30 days" for a study plan.
Interview Prep: E.g., "Give me interview questions for a software developer role at Meta" for a short quiz.


Interact:
Submit queries to get answers, plans, or quizzes.
Use Pomodoro timer and reminders in the sidebar.
View chat history in the sidebar’s expandable section.


Start Mock Interview:
Click “Attempt Your Mock Interview Now” in the sidebar to open the interview interface in a new tab.



Mock Interview Interface (http://localhost:8502)

Select Company and Role:
Choose a company (e.g., Meta, Google) from the alphabetically sorted dropdown.
Select a role (e.g., Software Engineer, Data Engineer) suitable for any engineering branch.
For “Other” company, enter a custom name.


Generate Questions:
Click “Generate Interview Questions” to fetch 50 unique, company-specific questions.
View a colorful mini-graph of past performance for the selected company/role.


Answer Questions:
Answer 10 questions per page using radio buttons.
Navigate with “Previous Page” and “Next Page”.
Click “Submit Answers” to see results.


View Results:
Displays score, questions, your answers, correct answers, and explanations.
Restart with a new set of questions via “Restart Interview”.



Example Outputs
Chatbot

Input: "What is the Pythagorean theorem?" (Question)
Output: "In a right-angled triangle, the square of the hypotenuse equals the sum of the squares of the other two sides: a² + b² = c²."


Input: "Learn Python in 30 days" (Goal)
Output: A 30-day study plan with tasks like variables, loops, and projects.


Input: "Interview questions for Meta" (Interview Prep)
Output: A 3-question quiz with options, correct answers, and feedback.



Mock Interview (Meta, Software Engineer)

Selection: Company: Meta, Role: Software Engineer
Performance Graph: Mini bar chart showing past scores (e.g., 70%, 80%) in orange/purple.
Questions (sample):
Q1: "Write a function to find the shortest path in a weighted graph."
Options: 1) Use a depth-first search approach, 2) Use a brute-force enumeration, 3) Rely on external libraries, 4) Implement a greedy algorithm
Correct: 1) Use a depth-first search approach


Q2: "Design a scalable notification system for Facebook."
Options: 1) Use a monolithic architecture, 2) Design a distributed system with sharding, 3) Avoid caching mechanisms, 4) Use a single database instance
Correct: 2) Design a distributed system with sharding




Results:
Score: 45/50 (90.00%)
Q1: Your Answer: 1) Correct Answer: 1) Explanation: Meta expects efficient algorithms like DFS for graph problems.
Q2: Your Answer: 2) Correct Answer: 2) Explanation: Meta’s system design focuses on scalability with sharding.



Technical Details

Tech Stack:
Python: Core language.
Streamlit: Web framework for both interfaces.
Transformers: t5-small for generating answers, options, and explanations.
googlesearch-python: Fetches company-specific questions from sources like Glassdoor and InterviewBit.
Pandas/Matplotlib: Performance tracking and visualization.


Data Storage:
chat_history.json: Stores chatbot interactions.
performance_history.json: Tracks mock interview scores with timestamps.


Design: White/orange/purple theme with fade-in animations for a modern UI.

Troubleshooting

Port Conflicts:
Check ports: netstat -aon | findstr :8502
Change port in app.py (e.g., port = 8503).


Web Search Issues:
Reduce num_results in quiz_generator.py to 30 if rate-limited.

Cache questions:
with open("questions_cache.json", "w") as f:
    json.dump(questions, f)




Model Performance:
Use t5-small for accuracy. Clear cache if memory is low:
python -c "from transformers import utils; utils.clean_cache()"




File Errors:
Ensure all files are in C:\Users\emeli\Music\AI Personal Study Coach\.qodo\.
Verify write permissions for chat_history.json and performance_history.json.



Future Enhancements

Add question difficulty levels (easy/medium/hard).
Export results to LaTeX-based PDF for offline review.
Integrate a timer per question to simulate interview pressure.

Note from the Developer
As a new learner, I built this project to explore Python, AI, and web development through an engaging, real-world application. By tackling challenges like web scraping, LLM integration, and UI design, I’ve gained hands-on experience while creating a tool to help others prepare for technical interviews. This project reflects my passion for learning and building impactful solutions.
