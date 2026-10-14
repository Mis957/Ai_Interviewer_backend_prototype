# परिSamvad (Parisamvad) Frontend

AI-powered conversational interview readiness web application built with **React**, **Vite**, and styled with an editorial typography-first design system connected to the FastAPI backend.

---

## Overview

**परिSamvad (Parisamvad)** is a voice and text interview practice platform designed to simulate realistic technical and behavioral interviews. The frontend features:
- **Redesigned Editorial Homepage**: Narrative scroll storytelling featuring interactive Hero with audio waveforms, Editorial Philosophy statement, Interactive Problem / Failure Mode explorer, 3-Phase How It Works, Deep Interview Preparation tracks (2x2 symmetrical layout), परिSamvad Experience with custom branding, transparent Pricing Tiers with custom pill controls, comprehensive FAQ accordion, and Final Call To Action.
- **Unified Typography & Aesthetics**: Editorial Bodoni serif display headings, Caveat handwritten accents with subtle swoops, warm ivory/bone light themes, and rich dark stage sections.
- **Candidate Setup Workflow (`/interview/new`)**: Dual-mode setup supporting Standard technical tracks (Target Role, Tech Stack, Years of Experience, Duration, Difficulty) and Resume-Based dynamic interviews (PDF/DOC/DOCX drag-and-drop upload).
- **Interactive Live Interview Room (`/interview/live`)**: Real-time voice recording via browser `MediaRecorder`, backend STT transcription, audio question playback (Edge-TTS / offline pyttsx3 fallback), dynamic difficulty scaling, and instant evaluation metrics.
- **Performance Evaluation & Reports**: Automated end-of-session evaluation scorecards covering technical accuracy, fluency, filler word counts, confidence ratings, and actionable improvement roadmaps.

---

## Frontend Stack

- **Framework**: React 18
- **Build Tool**: Vite 5
- **Language**: JavaScript (JSX)
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Styling**: Vanilla CSS (Custom design tokens, glassmorphism, responsive editorial grids)

---

## Application Structure

```text
frontend/
├── public/               # Public assets and favicon.svg
├── src/
│   ├── components/       # UI and shared components
│   │   ├── auth/         # Login & Signup form views
│   │   ├── home/         # Homepage sections:
│   │   │   ├── HomeHero.jsx               # Interactive hero with live waveform & audio preview
│   │   │   ├── StatementSection.jsx       # Editorial brand manifesto
│   │   │   ├── ProblemSection.jsx         # 3 interview failure mode cards
│   │   │   ├── HowItWorksSection.jsx      # 3-step timeline walkthrough
│   │   │   ├── InterviewPrepSection.jsx   # Primary spotlight + 4 secondary domain cards
│   │   │   ├── PracticeLoop.jsx           # परिSamvad brand showcase & stage
│   │   │   ├── PricingSection.jsx         # Free, Pro, and Annual tier cards with pill CTAs
│   │   │   ├── FaqSection.jsx             # Expandable Q&A accordion
│   │   │   ├── FinalCtaSection.jsx        # Dark theme final onboarding banner
│   │   │   ├── Footer.jsx                 # Editorial 4-column footer
│   │   │   ├── HandwrittenHighlight.jsx   # Shared handwritten Caveat accent with partial swoop
│   │   │   └── useScrollReveal.js         # IntersectionObserver scroll transition hook
│   │   ├── BrandWordmark.jsx              # Reusable Devanagari brand mark
│   │   ├── PerformanceReport.jsx          # Comprehensive final score report modal
│   │   └── Sidebar.jsx                    # Application dashboard sidebar navigation
│   ├── pages/            # Page-level route views
│   │   ├── Home.jsx                       # Homepage entrypoint assembling all sections
│   │   ├── Login.jsx & Signup.jsx         # Candidate authentication screens (UI preview)
│   │   ├── Overview.jsx                   # Dashboard overview with practice metrics
│   │   ├── InterviewDashboard.jsx         # Step-by-step interview configuration & resume upload
│   │   ├── InterviewLive.jsx              # Active interview room with audio controls & metrics
│   │   ├── History.jsx                    # Previous interview history (UI preview)
│   │   └── Settings.jsx                   # Audio and profile preferences (UI preview)
│   ├── services/
│   │   └── api.js                         # Axios backend API client
│   ├── styles.css        # Main editorial design system & landing page styling
│   ├── dashboard.css     # Dashboard & setup screen styles
│   ├── interview.css     # Live interview room styling
│   ├── auth.css          # Authentication screen styles
│   ├── laptop.css        # Responsive desktop/laptop overrides
│   ├── App.jsx           # Client router setup
│   └── main.jsx          # React app mounting point
├── package.json          # Dependencies and scripts
└── vite.config.js        # Vite build & dev server configuration
```

---

## Application Routes

- `/` — Homepage showcasing product narrative, preparation tracks, pricing, and FAQ.
- `/login` — Account sign-in (frontend preview interface).
- `/signup` — Account registration (frontend preview interface).
- `/dashboard` — Candidate dashboard displaying metrics and quick-start actions.
- `/interview/new` — Interview configuration (Standard role selection or Resume upload mode).
- `/interview/live` — Active live interview room (Voice capture, TTS playback, real-time evaluation).
- `/history` — Session history and past scorecards (frontend preview interface).
- `/settings` — Candidate settings and audio configuration (frontend preview interface).

---

## Backend Communication & API Integration

The frontend communicates with the FastAPI backend through `src/services/api.js`.

### Configuration
By default, the backend API URL is configured in `src/services/api.js`:
```javascript
const API_BASE_URL = 'http://127.0.0.1:8000';
```
*(No sensitive keys or secrets are stored in the client-side bundle.)*

### Integrated Endpoints
- **`GET /health`**: Verifies backend availability and database failover state.
- **`POST /interview/start`**: Initializes an interview session (accepts target role, technology, years of experience, difficulty, and optional uploaded resume file).
- **`POST /interview/answer`**: Submits voice recording (`audio/webm`, `audio/ogg`, or `audio/mp4`) or text answer with session and question IDs; returns transcription, numerical scores, actionable feedback, and the next question payload.
- **`POST /interview/end`**: Ends the session and returns overall technical score, communication score, confidence score, and roadmap recommendations.
- **`POST /resume/screen`**: Standalone resume parsing and ATS score evaluation.
- **`GET /analytics/learning`**: Question bank intelligence analytics.
- **`GET /audio/{filename}`**: Static route serving synthesized question audio.

---

## Development & Local Execution

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
The Vite development server runs at `http://localhost:3000` (or the port specified in `vite.config.js`).

Ensure the backend server is running concurrently:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Build for Production
To validate and generate optimized static assets:
```bash
npm run build
```
Compiled assets will output to `frontend/dist/`.

To preview the production build locally:
```bash
npm run preview
```

---

## Current Status & Known Scope

- **Authentication**: `/login` and `/signup` are currently UI preview components. JWT/OAuth backend session authentication is not yet integrated into the application state.
- **History & Settings**: `/history` and `/settings` display static mock state.
- **Audio & Live Interaction**: Voice interaction records candidate responses using browser `MediaRecorder` and sends audio blobs as `multipart/form-data` to `/interview/answer` for transcription and scoring. Question playback streams backend-generated audio. Continuous video streaming or 3D animated lip-sync avatars are not part of the current implementation.

