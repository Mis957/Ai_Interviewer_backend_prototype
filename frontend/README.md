# AI Interview Readiness Platform - React Frontend

The React Web Application frontend for the **AI Interview Readiness Platform**, featuring real-time Web Audio voice recording, Text-to-Speech audio playback, live difficulty badges, dynamic evaluation popups, and a backend self-learning dashboard.

---

## Features

1. **In-Browser Speech Recording (Speech-to-Text)**:
   - Uses Web Audio API (`MediaRecorder`) to record voice answers directly from microphone and stream audio blobs to the FastAPI backend.
2. **Text-to-Speech Audio Playback**:
   - HTML5 Audio player auto-plays synthesized question speech (`.mp3`).
3. **Dynamic Difficulty Badge**:
   - Real-time visual indicator showing current difficulty (`Easy` $\rightarrow$ `Medium` $\rightarrow$ `Hard`).
4. **Final Report & Learning Roadmap Dashboard**:
   - Visual performance cards for Technical Score, Communication Score, Confidence, and actionable learning steps.
5. **Backend Self-Learning Dashboard**:
   - Displays auto-curated questions learned by the backend from dynamic LLM generations.

---

## Setup & Running Guide

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
Open **`http://localhost:3000`** in your browser. (Ensure backend is running on `http://localhost:8000`).
