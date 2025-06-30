
# 📚 AI Personal Study Coach

![Streamlit](https://img.shields.io/badge/Built%20With-Streamlit-orange?logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Transformers](https://img.shields.io/badge/Transformers-HuggingFace-purple?logo=huggingface)
![Status](https://img.shields.io/badge/Project-Active-brightgreen)

> A Streamlit-based AI assistant that helps students and job seekers with interactive study planning, question answering, and realistic technical interview preparation.

---

## 🌟 Overview

**AI Personal Study Coach** is an interactive web app that:
- Answers technical and academic questions using LLMs and web search
- Generates structured study plans
- Conducts company-specific mock interviews with performance tracking

Built using **Streamlit**, **Transformers**, and **Google Search**, it provides dual interfaces:
- 🧠 **Chatbot (app.py)** — for answering questions, generating quizzes, Pomodoro timer, and study plans
- 💼 **Mock Interview (interview.py)** — for realistic interview simulation with 50 unique, role-specific questions

---

## 🧠 Developer Note

As a beginner in programming, I built this project to:
- Explore **Python**, **LLMs**, and **Streamlit**
- Solve real-world problems in interview prep
- Create engaging tools for learners like me

This project taught me about:
- API integration
- Web UI building
- Data visualization
- Prompt engineering & model selection

---

## ✨ Features

### 🧠 Chatbot Interface (http://localhost:8501)
- ✅ Question Answering using LLMs and Web Search (T5-small recommended)
- 📅 Study Plan Generator (e.g., "Learn Python in 30 days")
- 🧪 3-question Interview Quizzes with feedback
- ⏱️ Pomodoro Timer + Reminders for productivity
- 💬 Chat history saved to `chat_history.json`

### 💼 Mock Interview Interface (http://localhost:8502)
- 🎯 Company & Role Selection (Meta, Google, etc.)
- 🧩 50 Unique Questions from real sources (Glassdoor, InterviewBit)
- 📈 Performance Tracking with color-coded mini graphs
- 🧠 Explanations generated using LLMs
- 🔁 Pagination and Restart Interview options

---

## 📁 Project Structure

```
AI Personal Study Coach/.qodo/
├── app.py                   # Chatbot main app
├── interview.py             # Mock interview interface
├── quiz_generator.py        # Generates interview questions
├── study_assistant.py       # LLM + Web search logic
├── chat_history.py          # Chat history handler
├── chat_history.json        # Stores chatbot interactions
├── performance_history.json # Tracks interview scores
└── README.md                # Project documentation
```

---

## ⚙️ Setup Instructions

### 1. 📦 Install Dependencies
```bash
pip install streamlit transformers googlesearch-python pandas matplotlib python-dotenv
```

### 2. 🧠 Run the Chatbot
```bash
cd path/to/project/.qodo
streamlit run app.py
```
➡ Opens at: `http://localhost:8501`

### 3. 💼 Run the Mock Interview (optional, or via sidebar button)
```bash
streamlit run interview.py --server.port 8502
```
➡ Opens at: `http://localhost:8502`

---

## 🧪 Example Usage

### Chatbot
- `"What is the Pythagorean theorem?"` → Detailed explanation
- `"Learn Python in 30 days"` → Structured study plan
- `"Interview questions for Meta"` → Short quiz with feedback

### Mock Interview
- Select: `Company: Meta`, `Role: Software Engineer`
- Answer 10 questions per page (50 total)
- See detailed results + mini performance chart
- Sample Question:  
  Q: Design a notification system  
  ✅ Correct: Use distributed system with sharding

---

## 📊 Tech Stack

| Component | Tech |
|----------|------|
| Language | Python 3.10+ |
| UI | Streamlit |
| LLMs | Transformers (t5-small, gpt2, bart-large) |
| Search | googlesearch-python |
| Visualization | Matplotlib, Pandas |
| Storage | JSON files (`chat_history.json`, `performance_history.json`) |

---

## 🧩 Troubleshooting

- 🔁 **Port Conflicts**:  
  Run `netstat -aon | findstr :8502` to check active ports

- 🕵️‍♂️ **Web Search Limit**:  
  Lower `num_results` in `quiz_generator.py` if rate-limited

- 🧠 **Low Memory**:
  Use T5-small model  
  Clean cache:
  ```bash
  python -c "from transformers import utils; utils.clean_cache()"
  ```

---

## 🚀 Future Enhancements

- [ ] Add difficulty levels to questions
- [ ] Export results to PDF
- [ ] Add countdown timer for each interview question

---





## 🙌 Support

If you find this helpful:
⭐ Star the repo  
🐛 Report issues  
📬 Connect on [LinkedIn](https://www.linkedin.com/in/dipshikha4ai/)
