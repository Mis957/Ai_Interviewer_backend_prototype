# AI Interview Readiness Platform - Backend Engine

A deterministic, state-machine driven **AI Interview Engine** and **Resume Screening** backend built with **FastAPI**, **SQLAlchemy**, **Supabase PostgreSQL**, **Google Gemini AI / Groq AI**, **Edge-TTS**, and **Whisper (STT)** following clean architecture principles.

---

## 🌟 Key Features

- **Deterministic Interview Engine**: Backend state machine acting as the single source of truth for session state, question sequencing, and difficulty scaling (`Easy` ↔ `Medium` ↔ `Hard`).
- **AI Resume Screening & Evaluation**: Upload candidate resumes (`.pdf`, `.txt`, `.docx`) to extract candidate details, technical skills, projects, and receive an AI-generated assessment of **Strengths**, **Weaknesses / Skill Gaps**, **Overall Score (0-100)**, **Actionable Recommendations**, and **Suggested Technology Tracks**.
- **Scoped LLM Integration**: Used for answer evaluation, dynamic question fallback generation, final report synthesis, and resume screening.
- **Supabase PostgreSQL Connection**: Scalable, persistent database storage for curated questions, interview sessions, candidate responses, and generated questions.
- **Hybrid Question Selection**: Fetches pre-vetted domain questions from PostgreSQL first, falling back to LLM generation only when database questions for a topic/difficulty are exhausted.
- **Asynchronous Audio Pipeline**: Neural Text-To-Speech powered by `edge-tts` and optional Speech-To-Text via `whisper`.

---

## 🏗️ Clean Architecture Overview

```
Ai_Interviewer_backend_prototype/
├── app/
│   ├── core/
│   │   ├── config.py           # Environment settings & Pydantic BaseSettings
│   │   └── database.py         # SQLAlchemy engine, SessionLocal & Base
│   ├── models/
│   │   ├── question.py         # Question & GeneratedQuestion DB models
│   │   └── session.py          # InterviewSession & InterviewAnswer DB models
│   ├── schemas/
│   │   ├── question.py         # Question Pydantic v2 schemas
│   │   ├── interview.py        # Session, Answer, Eval & Final Report schemas
│   │   ├── resume.py           # Resume Screening Response schemas
│   │   └── audio.py           # Audio request/response payload schemas
│   ├── repositories/
│   │   ├── base.py             # Generic CRUD Base Repository
│   │   ├── question_repo.py    # Database queries for curated & generated questions
│   │   └── session_repo.py     # Database queries for sessions & answers
│   ├── services/
│   │   ├── gemini_service.py   # Gemini AI (Evaluation, Fallback Generation, Reports)
│   │   ├── resume_service.py   # Resume Parsing (PDF/TXT/DOCX) & AI Screening
│   │   ├── audio_service.py    # TTS (Edge-TTS) & STT (Whisper) services
│   │   ├── selection_service.py# Hybrid DB-first / LLM-fallback selection
│   │   └── engine_service.py   # State Machine Orchestrator & Difficulty scaling
│   ├── routers/
│   │   ├── interview.py        # /interview/* endpoints
│   │   ├── questions.py        # /questions/* endpoints
│   │   ├── resume.py           # /resume/* screening endpoints
│   │   └── analytics.py        # /analytics/* endpoints
│   └── main.py                 # FastAPI app entrypoint & CORS middleware
├── seed_data.py                # Pre-populated technical questions seed script
├── test_api.py                 # End-to-end integration test runner
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## ⚙️ Environment Configuration

Refer to the `.env.example` file for the `.env` configurations.

---

## 🚀 Quick Start & Local Execution Guide

### 1. Activate Virtual Environment

- **PowerShell (Windows)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Command Prompt (CMD)**:
  ```cmd
  venv\Scripts\activate
  ```
- **Linux / macOS**:
  ```bash
  source venv/bin/activate
  ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed Initial Question Bank

Populate Supabase PostgreSQL with initial curated domain questions:

```bash
python seed_data.py
```

### 4. Launch Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📖 API Documentation & Interactive UI

Once the server is running, access the interactive docs in your browser:

- 🟢 **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🔵 **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- ❤️ **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🎯 Key API Endpoints

### 1. Resume Screening & Analysis
`POST /resume/screen` *(Multipart Form Data)*
- `file`: Upload candidate resume file (`.pdf`, `.txt`, or `.docx`)

### 2. Start Interview Session
`POST /interview/start`
```json
{
  "user_id": "candidate_101",
  "technology": "Python",
  "initial_difficulty": "Easy"
}
```

### 3. Submit Answer (Text or Audio)
`POST /interview/answer` *(Form Data)*
- `session_id`: `<uuid>`
- `question_id`: `<uuid>`
- `candidate_answer`: `"A decorator is a wrapper function..."`
- `audio_file`: *(Optional audio file upload)*

### 4. Conclude Interview & Get Final Report
`POST /interview/end` *(Form Data)*
- `session_id`: `<uuid>`

Returns overall technical score, communication score, confidence rating, strong/weak topics, and a structured learning roadmap.

### 5. Manage Question Bank
- `GET /questions?technology=Python` — List questions by technology track
- `POST /questions` — Add a new curated technical question
- `GET /questions/random?limit=5` — Get a random question sample

---

## 📈 Difficulty Transition Rules

The state machine scales question difficulty based on evaluation scores:

- **Score ≥ 8.0**: Upgrade difficulty (`Easy` → `Medium` → `Hard`)
- **5.0 ≤ Score < 8.0**: Retain current difficulty level
- **Score < 5.0**: Downgrade difficulty (`Hard` → `Medium` → `Easy`)