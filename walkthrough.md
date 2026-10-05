# AI Interview Readiness Platform - Full Stack Walkthrough

## Executive Summary

The **AI Interview Readiness Platform** is now a fully functional full-stack solution featuring:
1. **React Web Application Frontend** (`Frontend_Prototype/`) running on `http://localhost:3000` with Web Audio in-browser recording (`MediaRecorder`), HTML5 TTS question playback, dynamic difficulty badges, real-time evaluation popups, and visual performance reports.
2. **Backend Adaptive Self-Learning System** (`Backend_Prototype/`) running on `http://localhost:8000` with an auto-curation engine that promotes high-performing LLM-generated questions into the permanent PostgreSQL/SQLite `questions` database table.

---

## 1. System Architecture & Component Mapping

```
AI Interview Readiness Platform
├── Backend (FastAPI - Port 8000)
│   ├── Clean Architecture (Routers -> Services -> Repositories -> Models)
│   ├── State Engine (Difficulty Escalation Rules: >=8 up, >=5 stay, <5 down)
│   ├── Gemini AI Integration (Answer Evaluation, Fallback Question Gen, Final Synthesis)
│   ├── Speech Engine (Whisper STT + Edge-TTS/offline pyttsx3 TTS)
│   └── Self-Learning Engine (Auto-promotes generated questions score >= 5 to Question Bank)
│
└── Frontend (Vite + React - Port 3000)
    ├── Navbar.jsx               # Header with live backend connection status indicator
    ├── TechnologySelector.jsx   # Select track (Python, Java, DBMS, ML, etc.) & starting level
    ├── InterviewStudio.jsx      # Microphone recorder, TTS audio replay, difficulty badges
    ├── EvaluationModal.jsx      # Real-time score, feedback, missing topics popup
    ├── PerformanceReport.jsx    # Technical/Communication score cards & Learning Roadmap
    └── LearnedInsights.jsx      # Self-learning dashboard & auto-curated questions view
```

---

## 2. Verified Test Results & Live URLs

- **React Frontend**: `http://localhost:3000`
- **FastAPI Backend Swagger Docs**: `http://localhost:8000/docs`
- **Backend Health Check**: `http://localhost:8000/health`
- **Self-Learning Analytics Endpoint**: `http://localhost:8000/analytics/learning`

---

## 3. How to Run & Test both Frontend and Backend

### Step 1: Start Backend (Port 8000)
```powershell
cd c:\Minor_Project\Backend_Prototype
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Step 2: Start Frontend (Port 3000)
```powershell
cd c:\Minor_Project\Backend_Prototype\frontend
npm run dev
```

### Step 3: Experience the Interview Flow
1. Open `http://localhost:3000`.
2. Select a **Technology Track** (e.g. Python, DBMS) and click **Start Interview**.
3. Listen to the automatically synthesized question audio or click **Record Voice Response** to speak your answer via microphone.
4. Click **Submit Answer** to see instant Gemini feedback, missing concepts, and difficulty shifts.
5. Review your final **Performance Report** and **Learning Roadmap** upon interview completion.
6. Check **Learned Insights** tab to see how the backend auto-curated questions into the Question Bank database!
