import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.engine_service import InterviewEngineService
from app.services.audio_service import AudioService
from app.schemas.interview import (
    InterviewMode,
    DifficultyLevel,
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
    mode: InterviewMode = Form(InterviewMode.STANDARD, description="Interview mode: Select 'standard' or 'resume' from dropdown"),
    user_id: Optional[str] = Form("candidate_123", description="Candidate ID"),
    
    # Standard Mode Parameters
    technology: Optional[str] = Form("Python", description="[Standard Mode] Technology track (Python, Java, DBMS, etc.)"),
    target_role: Optional[str] = Form("Software Developer", description="[Standard Mode] Target Job Role (e.g. Software Developer, Backend Engineer, Fullstack)"),
    years_of_experience: Optional[str] = Form("0", description="[Standard Mode] Years of experience (e.g., '0' for Fresher, '2', '5+')"),
    initial_difficulty: DifficultyLevel = Form(DifficultyLevel.EASY, description="[Standard Mode] Initial question difficulty: Select Easy | Medium | Hard from dropdown"),
    
    # Resume Mode Parameters
    resume_text: Optional[str] = Form(None, description="[Resume Mode] Optional raw resume text"),
    file: Optional[UploadFile] = File(None, description="[Resume Mode] Candidate resume file upload (.pdf, .txt, .docx)"),
    
    db: Session = Depends(get_db)
):
    """
    Start a new interview session (Standard or Resume-Based).
    
    - **mode**: Dropdown select `standard` or `resume`.
    - **Standard Mode Parameters**: `technology`, `target_role`, `years_of_experience`, `initial_difficulty`.
    - **Resume Mode Parameters**: `file` (resume upload) or `resume_text`.
    """
    try:
        engine = InterviewEngineService(db)
        
        file_bytes = None
        filename = None
        if file and hasattr(file, "read"):
            file_bytes = await file.read()
            filename = getattr(file, "filename", "resume.pdf")

        mode_val = mode.value if isinstance(mode, InterviewMode) else str(mode)
        diff_val = initial_difficulty.value if isinstance(initial_difficulty, DifficultyLevel) else str(initial_difficulty)

        req = InterviewStartRequest(
            user_id=user_id or "candidate_123",
            mode=mode_val,
            technology=technology or "Python",
            target_role=target_role or "Software Developer",
            years_of_experience=years_of_experience or "0",
            initial_difficulty=diff_val,
            resume_text=resume_text
        )

        return await engine.start_interview(
            req=req,
            file_bytes=file_bytes,
            filename=filename
        )
    except Exception as e:
        logger.exception("start_interview failed: %s", e)
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
    if audio_path and os.path.exists(audio_path):
        question_payload.audio_url = f"/audio/{os.path.basename(audio_path)}"
    else:
        question_payload.audio_url = None
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

        # Sanitize IDs
        question_id = question_id.strip() if question_id and question_id.strip() not in ("", "null", "None") else None
        generated_question_id = generated_question_id.strip() if generated_question_id and generated_question_id.strip() not in ("", "null", "None") else None

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
            raise HTTPException(status_code=400, detail="No speech detected in your recording. Please check your microphone and speak clearly.")

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

@router.post("/evaluate-audio", response_model=AnswerEvaluationResponse)
async def evaluate_audio_answer(
    session_id: str = Form(...),
    question_id: Optional[str] = Form(None),
    generated_question_id: Optional[str] = Form(None),
    audio_file: UploadFile = File(..., description="Candidate speech audio file (.mp3, .wav, .m4a, .webm)"),
    db: Session = Depends(get_db)
):
    """
    Dedicated Audio Evaluation API:
    1. Transcribes candidate spoken response using Groq Whisper API (whisper-large-v3-turbo).
    2. Evaluates response quality against expected answer using LLM.
    3. Updates interview session state and returns next question with TTS audio.
    """
    try:
        engine = InterviewEngineService(db)
        audio_service = AudioService()
        
        # Sanitize IDs
        question_id = question_id.strip() if question_id and question_id.strip() not in ("", "null", "None") else None
        generated_question_id = generated_question_id.strip() if generated_question_id and generated_question_id.strip() not in ("", "null", "None") else None
        
        # Save audio file
        import uuid
        ext = os.path.splitext(audio_file.filename)[1] or ".mp3"
        temp_filename = f"audio_ans_{uuid.uuid4().hex[:8]}{ext}"
        save_path = os.path.join(audio_service.storage_dir, temp_filename)
        with open(save_path, "wb") as buffer:
            buffer.write(await audio_file.read())

        # Speech-To-Text via Groq Whisper API
        transcribed_text = audio_service.speech_to_text(save_path)
        if not transcribed_text.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio response. Please speak clearly and try again.")

        return await engine.submit_answer(
            session_id=session_id,
            question_id=question_id,
            generated_question_id=generated_question_id,
            candidate_answer=transcribed_text,
            candidate_audio_path=save_path
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
