# 🤖 AI DevOps Assistant

An AI-powered DevOps chatbot and copilot built with **React**, **FastAPI**, **Google Gemini**, **LangChain**, and **ChromaDB**. It helps developers understand DevOps concepts, troubleshoot issues, retrieve knowledge, and safely interact with DevOps tools such as Docker, Git, and Kubernetes.

---
<img width="1340" height="621" alt="image" src="https://github.com/user-attachments/assets/5fce0796-8c11-45d1-8e60-087075259c77" />




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
```


## 🚀 How to Use

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-devops-assistant.git
cd ai-devops-assistant
```
### 2. Setup Backend
```
cd backened
python -m venv venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Gemini API

Create a .env file inside the backened folder:

GEMINI_API_KEY=your_gemini_api_key_here

⚠️ Never share or commit your API key.

### 4. Build the Knowledge Base

Run the following command from the backened folder:

python ai/ingest.py

This creates the local ChromaDB knowledge base from the DevOps documentation.

### 5. Start the Backend
```
uvicorn main:app --reload
```
Backend will run at:
```
http://127.0.0.1:8000
```
### 6. Start the Frontend

Open a new terminal and run:
```
cd ai-devops-assistant/frontend
npm install
npm run dev
```
The frontend will normally run at:
```
http://localhost:5173
```
### 7. Open the Application

Open the frontend URL in your browser:

http://localhost:5173


