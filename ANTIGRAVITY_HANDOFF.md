
# PREPTALK — ANTIGRAVITY HANDOFF

## Current milestone
Milestone 1B

## Objective
Convert the existing Milestone 1 live interview into a natural,
continuous adaptive interviewer experience.

## NON-NEGOTIABLE
DO NOT MODIFY BACKEND.

app/** is READ-ONLY.

Backend files modified: 0.

## Current desired flow

START
→ AI asks
→ TTS
→ candidate answers
→ real microphone
→ MediaRecorder Blob
→ /interview/answer
→ silent evaluation
→ backend next_question
→ backend next_difficulty
→ TTS
→ next answer
→ repeat

## Critical corrections

1. EvaluationModal must NOT interrupt every answer.
2. No manual "Next Question" during normal flow.
3. No score toast.
4. No frontend adaptive algorithm.
5. Backend owns adaptive difficulty.
6. Consume response.next_question.
7. Observe response.next_difficulty.
8. Do not assume Easy → Medium → Hard.
9. Preserve PrepTalk UI.
10. Do not use InterviewStudio dark UI.
11. Save & Exit is out of scope.
12. Hedra is out of scope.
13. ElevenLabs is out of scope.
14. No backend changes.
15. No new unnecessary dependencies.

## Backend APIs

POST /interview/start
POST /interview/answer
POST /interview/end
GET /audio/{filename}

## Milestone 2
Do NOT implement final PerformanceReport yet.

## Required final verification

npm run build

git status
git diff
git diff -- app

No commit.
No push.