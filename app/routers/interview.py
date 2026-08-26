import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.engine_service import InterviewEngineService
from app.services.audio_service import AudioService
from app.schemas.interview import (
    InterviewStartRequest,
    InterviewStartResponse,
    SubmitAnswerRequest,
    AnswerEvaluationResponse,
    NextQuestionPayload,
    FinalReportResponse
)

router = APIRouter(prefix="/interview", tags=["Interview Engine"])

@router.post("/start", response_model=InterviewStartResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    payload: InterviewStartRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new interview session for a given technology.
    Retrieves the first question (from DB or dynamically generated via Gemini) and generates TTS audio.
    """
    try:
        engine = InterviewEngineService(db)
        return await engine.start_interview(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/question", response_model=NextQuestionPayload)
async def get_current_question(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetches the current active or next question for an ongoing session.
    """
    engine = InterviewEngineService(db)
    session = engine.session_repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    
    question_payload = engine.selection_service.select_next_question(
        session_id=session.id,
        technology=session.technology,
        difficulty=session.current_difficulty
    )
    audio_path = await engine.audio_service.text_to_speech(question_payload.question_text)
    question_payload.audio_url = audio_path
    return question_payload

@router.post("/answer", response_model=AnswerEvaluationResponse)
async def submit_answer(
    session_id: str = Form(...),
    question_id: Optional[str] = Form(None),
    generated_question_id: Optional[str] = Form(None),
    candidate_answer: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Submit candidate answer either via text or audio recording (STT using Whisper).
    Triggers Gemini answer evaluation, updates interview state & difficulty, and returns next question.
    """
    try:
        engine = InterviewEngineService(db)
        audio_service = AudioService()
        audio_path = None
        final_text_answer = candidate_answer or ""

        # Process audio file if uploaded
        if audio_file:
            temp_filename = f"upload_{audio_file.filename}"
            save_path = os.path.join(audio_service.storage_dir, temp_filename)
            with open(save_path, "wb") as buffer:
                buffer.write(await audio_file.read())
            audio_path = save_path
            
            # Convert speech to text using Whisper
            transcribed_text = audio_service.speech_to_text(save_path)
            if transcribed_text:
                final_text_answer = transcribed_text

        if not final_text_answer.strip():
            raise HTTPException(status_code=400, detail="Candidate answer text or audio recording is required.")

        return await engine.submit_answer(
            session_id=session_id,
            question_id=question_id,
            generated_question_id=generated_question_id,
            candidate_answer=final_text_answer,
            candidate_audio_path=audio_path
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/end", response_model=FinalReportResponse)
async def end_interview(
    session_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Concludes the interview session and generates a comprehensive final performance report
    with technical scores, communication ratings, strong/weak topics, and a learning roadmap.
    """
    try:
        engine = InterviewEngineService(db)
        return engine.generate_final_report(session_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
