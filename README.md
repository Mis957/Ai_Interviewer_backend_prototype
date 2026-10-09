# AI Interview Readiness Platform - Backend Engine

A deterministic, state-machine driven **AI Interview Engine** and **Resume Screening** backend built with **FastAPI**, **SQLAlchemy**, **Supabase PostgreSQL**, **Google Gemini AI / Groq AI**, **Edge-TTS with offline pyttsx3 fallback**, and **Whisper (STT)** following clean architecture principles.

---

## 🌟 Key Features

- **Deterministic Interview Engine**: Backend state machine acting as the single source of truth for session state, question sequencing, and difficulty scaling (`Easy` ↔ `Medium` ↔ `Hard`).
- **Dual Interview Modes (`standard` & `resume`)**:
  - **Standard Mode (`mode="standard"`)**: Practice domain-specific technical tracks (Python, Java, DBMS, Fullstack Web Development, etc.) tailored to candidate's **Target Job Role** (e.g., `Software Developer`, `Backend Architect`) and **Years of Experience** (e.g., `0` for Fresher, `2`, `5+`).
  - **Resume-Based Mode (`mode="resume"`)**: Practice dynamically generated questions based on uploaded candidate resumes (projects, project technologies, core skills, and HR/behavioral scenarios).
- **Interactive OpenAPI / Swagger UI Dropdowns**: Native Python Enums for `mode` (`standard` | `resume`) and `initial_difficulty` (`Easy` | `Medium` | `Hard`) rendering interactive dropdown menus in Swagger UI.
- **Adaptive Topic Rotation**: In Resume-Based mode, if candidate struggles ($\text{Score} < 5.0$), the engine rotates topics (`Project` $\rightarrow$ `HR/Behavioral` $\rightarrow$ `Skill`) at `Easy` level so candidate covers their entire resume without getting stuck on a single failing topic.
- **AI Resume Screening & Evaluation**: Upload candidate resumes (`.pdf`, `.txt`, `.docx`) to extract details, technical skills, projects, and receive an AI-generated assessment of **Strengths**, **Weaknesses / Skill Gaps**, **Overall Score (0-100)**, **Actionable Recommendations**, and **Suggested Technology Tracks**.
- **Supabase PostgreSQL & Offline Supabase Failover**: Uses hosted PostgreSQL when available, then fails over to local Supabase PostgreSQL on connection loss. The local database receives the same SQLAlchemy schema automatically.
- **Hybrid Question Selection**: Checks pre-vetted domain questions from the database first, falling back to LLM dynamic generation only when database questions are exhausted, saving newly generated questions to the database automatically.
- **Speech Pipeline**: Text-to-speech prefers `edge-tts` and falls back to offline `pyttsx3` using an installed system voice; speech-to-text uses Groq Whisper API with a local Whisper fallback.

---

## 🏗️ Clean Architecture Overview

```
Ai_Interviewer_backend_prototype/
├── app/
│   ├── core/
│   │   ├── config.py           # Environment settings & Pydantic BaseSettings
│   │   └── database.py         # SQLAlchemy engine, SessionLocal & auto-schema migrations
│   ├── models/
│   │   ├── question.py         # Question & GeneratedQuestion DB models
│   │   └── session.py          # InterviewSession & InterviewAnswer DB models
│   ├── schemas/
│   │   ├── question.py         # Question Pydantic v2 schemas
│   │   ├── interview.py        # Session, Answer, Eval & Final Report schemas
│   │   ├── resume.py           # Resume Screening Response schemas
│   │   └── audio.py            # Audio request/response payload schemas
│   ├── repositories/
│   │   ├── base.py             # Generic CRUD Base Repository
│   │   ├── question_repo.py    # Database queries for curated & generated questions
│   │   └── session_repo.py     # Database queries for sessions & answers
│   ├── services/
│   │   ├── gemini_service.py   # Groq / Gemini AI (Evaluation, Dynamic Generation, Reports)
│   │   ├── resume_service.py   # Resume Parsing (PDF/TXT/DOCX) & AI Screening
│   │   ├── audio_service.py    # TTS (Edge-TTS/offline pyttsx3) & STT (Groq/local Whisper)
│   │   ├── selection_service.py# Hybrid DB-first / LLM-fallback & Adaptive Topic Rotation
│   │   └── engine_service.py   # State Machine Orchestrator & Difficulty scaling
│   ├── routers/
│   │   ├── interview.py        # /interview/* endpoints (start, answer, evaluate-audio, end)
│   │   ├── questions.py        # /questions/* endpoints
│   │   ├── resume.py           # /resume/* screening endpoints
│   │   └── analytics.py        # /analytics/* endpoints
│   └── main.py                 # FastAPI app entrypoint & CORS middleware
├── seed_data.py                # Pre-populated technical questions seed script
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## ⚙️ Environment Configuration

Refer to `.env.example` for the complete environment-variable template. Copy it to `.env` and replace the provider and hosted database placeholders with your own values:

```powershell
Copy-Item .env.example .env
```

### Local Supabase Offline Database

Set `DATABASE_URL` in `.env` to your hosted Supabase PostgreSQL connection string and `OFFLINE_DATABASE_URL` to the local Supabase PostgreSQL connection string. The example uses Supabase's transaction pooler format for the hosted URL; replace its project, region, and password placeholders with your own values. The local URL uses Supabase CLI's local Postgres service and the default port `54322` from `supabase/config.toml`.

Keep `.env` private and never commit it. Only `.env.example` belongs in the repository; it contains placeholders, not credentials. The application defaults to SQLite if `DATABASE_URL` is not set; SQLite mode does not use hosted/local failover. Configure a hosted PostgreSQL URL to enable failover. Before launching the backend with a hosted URL, start Docker Desktop and the local Supabase stack:

```powershell
npx --yes supabase start
```

The backend writes to hosted Supabase while it is reachable. If the hosted database connection fails, it writes to local Supabase instead. A background check retries the hosted connection every 30 seconds; once it is reachable, rows from the local database are upserted to hosted Supabase. Local rows are retained after synchronization, and retries are safe if synchronization is interrupted. Check `/health` for the active database, the `offline_database` flag, and the `offline_sync` status (`not_configured`, `not_attempted`, `waiting_for_connection`, `pending`, or `synced`).

Only records present in the local database are sent to hosted Supabase during recovery; online records are not automatically copied down to local Supabase. Starting the backend with no internet therefore requires Docker and the local Supabase stack to be running.

### Offline Text-to-Speech

Question audio is generated with Edge TTS when its online service is reachable. If it is unavailable, the backend uses `pyttsx3` and a speech voice installed on the operating system to generate a local WAV file. On Windows, this uses the installed Windows SAPI voices; the offline voice may sound different from Edge's neural voice. Whisper is used for speech-to-text and cannot synthesize speech. Install Python dependencies with `python -m pip install -r requirements.txt`.

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

Populate database with initial curated domain questions:

```bash
python seed_data.py
```

### 4. Launch Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 📖 API Documentation & Interactive UI

Once the server is running, access the interactive documentation in your browser:

- 🟢 **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🔵 **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- ❤️ **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🎯 Key API Endpoints

### 1. Resume Screening & Analysis
`POST /resume/screen` *(Multipart Form Data)*
- `file`: Upload candidate resume file (`.pdf`, `.txt`, or `.docx`)

**Sample Response**:
```json
{
  "candidate_name": "Jane Developer",
  "overall_score": 88.0,
  "strengths": [
    "Strong technical skill set identified: Python, FastAPI, PostgreSQL, React, Docker.",
    "Demonstrated work experience with microservices architecture and high availability.",
    "Effective use of quantitative achievements and performance metrics."
  ],
  "weaknesses": [
    "Lacks explicit mention of Cloud Deployment platforms (AWS, GCP, Azure).",
    "Could expand on automated unit testing frameworks and CI/CD pipelines."
  ],
  "key_skills": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "React",
    "Docker"
  ],
  "recommendations": [
    "Incorporate measurable outcomes (STAR format: Situation -> Action -> Impact) for all roles.",
    "Highlight hands-on experience with cloud infrastructure or CI/CD pipelines."
  ],
  "suggested_technologies": [
    "Python",
    "DBMS",
    "Machine Learning"
  ]
}
```

---

### 2. Start Interview Session
`POST /interview/start` *(Form Data)*

Choose the interview mode using the `mode` parameter: **Standard** or **Resume-Based**.

#### Mode 1: Standard Mode (`mode="standard"`)
Start a domain-specific interview tailored to target role and experience:
* **Parameters**:
  - `mode`: `"standard"` *(Dropdown Enum: standard | resume)*
  - `user_id`: `"candidate_101"`
  - `technology`: `"Python"`
  - `target_role`: `"Software Developer"` *(Default: Software Developer)*
  - `years_of_experience`: `"0"` *(Default: 0 for Fresher)*
  - `initial_difficulty`: `"Easy"` *(Dropdown Enum: Easy | Medium | Hard)*

#### Mode 2: Resume-Based Mode (`mode="resume"`)
Start an adaptive interview tailored to the candidate's uploaded resume:
* **Parameters**:
  - `mode`: `"resume"` *(Dropdown Enum: standard | resume)*
  - `user_id`: `"candidate_101"`
  - `initial_difficulty`: `"Easy"` *(Dropdown Enum: Easy | Medium | Hard)*
  - `file`: *(Upload candidate `.pdf`, `.txt`, or `.docx` file)*
  - `resume_text`: *(Optional plain text resume if not uploading file)*

**Sample Response (`HTTP 201 Created`)**:
```json
{
  "session_id": "a0b25a05-7ab8-4b06-8587-bc57a006a249",
  "user_id": "candidate_101",
  "technology": "Python",
  "target_role": "Software Developer",
  "years_of_experience": "0",
  "mode": "standard",
  "status": "STARTED",
  "current_difficulty": "Easy",
  "first_question": {
    "question_id": "123e4567-e89b-12d3-a456-426614174000",
    "generated_question_id": null,
    "technology": "Python",
    "topic": "Decorators & Functions",
    "difficulty": "Easy",
    "question_text": "What is a decorator in Python and how do you write a custom function wrapper?",
    "audio_url": "./audio_storage/tts_3159ed8fe8c5.mp3",
    "is_llm_generated": false,
    "question_category": null
  }
}
```

---

### 3. Submit Answer (Text or Audio)
`POST /interview/answer` *(Form Data)*
- `session_id`: `<uuid>`
- `question_id`: `<uuid>` *(or `generated_question_id`)*
- `candidate_answer`: `"A decorator is a wrapper function..."`
- `audio_file`: *(Optional audio file upload)*

**Sample Response**:
```json
{
  "answer_id": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "session_id": "a0b25a05-7ab8-4b06-8587-bc57a006a249",
  "transcribed_text": "A decorator is a wrapper function...",
  "score": 8.5,
  "confidence_score": 9.0,
  "feedback": "Clear explanation of wrapper functions and @decorator syntax.",
  "fluency_feedback": "Fluent delivery with clear expression.",
  "filler_words_detected": [],
  "missing_topics": [],
  "current_difficulty": "Easy",
  "next_difficulty": "Medium",
  "next_question": {
    "question_text": "Next interview question...",
    "audio_url": "./audio_storage/tts_next.mp3"
  },
  "session_completed": false
}
```

---

### 4. Conclude Interview & Get Final Report
`POST /interview/end` *(Form Data)*
- `session_id`: `<uuid>`

Returns overall technical score, communication score, confidence rating, strong/weak topics, detailed Q&A history, and a structured learning roadmap.

---

### 5. Manage Question Bank & Analytics
- `GET /questions?technology=Python` — List questions by technology track
- `POST /questions` — Add a new curated technical question
- `GET /questions/random?limit=5` — Get a random question sample
- `GET /analytics/learning` — Get self-learning auto-curation analytics

---

## 📈 Difficulty Transition & Adaptive Topic Rotation Rules

- **Resume interview order**: Candidate introduction → questions about resume projects (up to five when there are multiple projects; three for one project) → technical questions drawn from listed skills and project tech stacks.
- **Score ≥ 8.0**: Ask a harder or deeper next question (`Hard`), including a focused follow-up where appropriate.
- **5.0 ≤ Score < 8.0**: Set the next question to `Medium` and build on demonstrated knowledge.
- **Score < 5.0**: Set the next question to `Easy` and revisit the area at a more foundational level without repeating the exact question.
- In the technical phase, rotate through each technology and progress its questions from fundamentals toward advanced topics. The latest answer score guides the next question's difficulty and depth.

---

## 🏁 Interview Termination Criteria

The interview practice session concludes based on the following criteria:

1. **Manual Termination**: Candidate clicks **"END SESSION"** button at any time to conclude the interview and view their evaluation report.
2. **Timer Expiration**: Session countdown timer reaches `00:00`.
   - Candidate can choose **"End Interview & Get Report"** to conclude the session.
   - *Alternatively, the candidate can choose to extend time by +5, +10, or +15 mins to continue practicing.*