# PrepTalk Frontend

AI-powered interview readiness web application for technical interview practice, powered by React, Vite, and FastAPI.

---

## Overview

PrepTalk is an interactive frontend application designed for AI-driven technical interview preparation. It provides real-time voice and text interview sessions, dynamic difficulty scaling, instant answer evaluations, performance analytics, and resume-based adaptive interview generation.

---

## Frontend Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: JavaScript (JSX)
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Styling**: Custom Vanilla CSS (Modern Dark/Glassmorphism theme)

---

## Frontend Structure

```text
frontend/
├── src/
│   ├── components/       # Reusable components (Sidebar, PerformanceReport, UI elements)
│   │   ├── auth/         # Login & Signup forms
│   │   └── home/         # Landing page hero & showcase components
│   ├── pages/            # Application views (Home, Overview, InterviewSetup, Live, History, Settings)
│   ├── services/         # API integration layer (api.js)
│   ├── data/             # Static navigation & fallback data
│   ├── styles.css        # Main design system & global styles
│   ├── dashboard.css     # Overview dashboard styling
│   ├── interview.css     # Live interview screen & control styles
│   ├── auth.css          # Auth forms styling
│   ├── App.jsx           # Application routing configuration
│   └── main.jsx          # React entrypoint
├── index.html            # HTML layout
├── package.json          # Project dependencies & scripts
└── vite.config.js        # Vite configuration
```

---

## Application Routes

- `/` — Landing page showcasing features and call-to-action
- `/login` — Login page (Mock UI interface)
- `/signup` — Account registration (Mock UI interface)
- `/dashboard` — Overview dashboard displaying metrics and quick actions
- `/interview/new` — Interview setup (Standard role/tech selection or Resume upload mode)
- `/interview/live` — Active interactive interview room (Voice recording, TTS playback, analysis)
- `/history` — Past interview history and session records (Mock UI representation)
- `/settings` — User preferences and audio configuration (Mock UI representation)

---

## Backend Integration

The frontend connects directly to the FastAPI backend service via `src/services/api.js`. Integrated endpoints include:

- **`GET /health`**: Backend service status check.
- **`POST /interview/start`**: Initializes an interview session (supports target role, technology, experience level, difficulty, and optional resume payload).
- **`POST /interview/answer`**: Submits candidate response (audio blob or text) with session ID and question context; receives detailed answer evaluation and next question payload.
- **`POST /interview/end`**: Finalizes the session and computes overall performance scores, strengths, and recommendations.
- **`POST /resume/screen`**: Standalone PDF resume analysis and feedback generation.
- **`GET /analytics/learning`**: Fetches backend self-learning question analytics.

---

## Interview Flow

1. **Setup & Configuration**: Select technology, target role, experience level, or upload a resume.
2. **Session Start**: Backend generates the initial question and synthesized TTS audio.
3. **Question & TTS Playback**: Candidate listens to question audio or reads the question prompt.
4. **Answer Submission**: Candidate records voice via browser `MediaRecorder` or inputs text answer.
5. **Real-time Analysis**: Backend evaluates answer accuracy, relevance, technical correctness, and adjusts question difficulty dynamically.
6. **Next Question Prompt**: Updated difficulty badge and new question loaded.
7. **Session Completion & Report**: Detailed performance breakdown displaying technical score, communication score, confidence score, key strengths, and actionable learning steps.

---

## Resume Integration

- **Resume-based Adaptive Mode**: Candidates can upload PDF resumes or paste resume text during interview setup (`/interview/new`).
- **Standalone Resume Screening**: Upload resume files to receive structured feedback on formatting, keywords, and skill match.

---

## Development Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:3000` (or Vite's designated port).

Ensure the FastAPI backend is running locally at `http://127.0.0.1:8000`.

---

## Backend Configuration

The backend API URL is configured in `src/services/api.js`:
```javascript
const API_BASE_URL = 'http://127.0.0.1:8000';
```

---

## Build Commands

- **Development Server**: `npm run dev`
- **Production Build**: `npm run build`
- **Preview Build**: `npm run preview`
- **Linter**: `npm run lint`

---

## Current Limitations

- **Authentication**: Login and Signup routes are UI components; backend user authentication (JWT/OAuth) is not yet integrated.
- **History & Settings**: History and Settings pages use UI representations and static state.
- **Save & Exit**: In-progress interview saving is not supported.
- **Interaction Step**: Questions proceed sequentially via explicit Answer $\rightarrow$ Stop Recording $\rightarrow$ Analysis $\rightarrow$ Next Question controls.
- **Avatar / Continuous Stream**: Live lip-sync avatar features (e.g. Hedra / ElevenLabs) are not implemented.
