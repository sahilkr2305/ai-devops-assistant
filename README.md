# 🤖 AI DevOps Assistant

An AI-powered DevOps chatbot and copilot built with **React**, **FastAPI**, **Google Gemini**, **LangChain**, and **ChromaDB**. It helps developers understand DevOps concepts, troubleshoot issues, retrieve knowledge, and safely interact with DevOps tools such as Docker, Git, and Kubernetes.

---

## 🔗 Live Demo

👉 Coming soon

---

## ✨ Features

- 🤖 AI-powered DevOps chatbot using **Google Gemini**
- 🧠 RAG-based knowledge retrieval using **ChromaDB**
- 💬 Conversation memory using **SQLite**
- 🐳 Docker environment inspection and operations
- 🌿 Git repository inspection
- ☸️ Kubernetes cluster and resource inspection
- 🔐 Safety layer for potentially dangerous operations
- ✅ Approval workflow before sensitive actions
- 📋 Audit logging for tool operations
- ⚡ Streaming AI responses using **Server-Sent Events (SSE)**
- 📱 Responsive React-based chatbot interface
- 📚 DevOps knowledge base covering Docker, Kubernetes, Git, CI/CD, AWS, and Terraform

---

## 🛠️ Tech Stack

- **Frontend:** React, Vite, JavaScript, CSS
- **Backend:** Python, FastAPI
- **AI:** Google Gemini, LangChain
- **RAG:** ChromaDB, Sentence Transformers
- **Database:** SQLite, SQLAlchemy
- **DevOps:** Docker, Git, Kubernetes
- **Communication:** REST API, Server-Sent Events (SSE)
- **Security:** Safety checks, approval workflow, audit logging

---

## 🏗️ How It Works

```text
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
 ┌──────────────────────────────┐
 │                              │
 ▼                              ▼
Google Gemini                ChromaDB
AI Reasoning                 RAG Knowledge
 │                              │
 └──────────────┬───────────────┘
                ↓
         DevOps Tool Layer
        ┌───────┼────────┐
        ↓       ↓        ↓
     Docker    Git    Kubernetes
                ↓
        Safety & Approval
                ↓
           Audit Logging

💡 How to Use AI DevOps Assistant

Once the backend and frontend are running, open the chatbot in your browser and interact with it using natural-language DevOps commands or questions.

1. Start the Backend
cd backened
source venv/Scripts/activate
uvicorn main:app --reload

Backend runs at:

http://127.0.0.1:8000
2. Start the Frontend

Open a second terminal:

cd frontend
npm run dev

Open the Vite URL shown in the terminal, usually:

http://localhost:5173
