import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.session_repo import InterviewSessionRepository, InterviewAnswerRepository
from app.repositories.question_repo import QuestionRepository, GeneratedQuestionRepository
from app.services.gemini_service import GeminiService
from app.services.audio_service import AudioService
from app.services.selection_service import QuestionSelectionService
from app.schemas.interview import (
    InterviewStartRequest,
    InterviewStartResponse,
    AnswerEvaluationResponse,
    NextQuestionPayload,
    FinalReportResponse
)

logger = logging.getLogger(__name__)

class InterviewEngineService:
    DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]
    MAX_QUESTIONS_PER_SESSION = 5

    def __init__(self, db: Session):
        self.db = db
        self.session_repo = InterviewSessionRepository(db)
        self.answer_repo = InterviewAnswerRepository(db)
        self.question_repo = QuestionRepository(db)
        self.gen_q_repo = GeneratedQuestionRepository(db)
        self.gemini_service = GeminiService()
        self.audio_service = AudioService()
        self.selection_service = QuestionSelectionService(
            self.question_repo,
            self.gen_q_repo,
            self.answer_repo,
            self.gemini_service
        )

    def _determine_next_difficulty(self, current_difficulty: str, score: float) -> str:
        """
        Difficulty Escalation Rules:
        If score >= 8: increase difficulty
        If score >= 5: keep same difficulty
        If score < 5: reduce difficulty
        """
        curr_idx = self.DIFFICULTY_LEVELS.index(current_difficulty) if current_difficulty in self.DIFFICULTY_LEVELS else 0
        
        if score >= 8.0:
            next_idx = min(curr_idx + 1, len(self.DIFFICULTY_LEVELS) - 1)
        elif score >= 5.0:
            next_idx = curr_idx
        else:
            next_idx = max(curr_idx - 1, 0)

        return self.DIFFICULTY_LEVELS[next_idx]

    async def start_interview(
        self,
        req: InterviewStartRequest,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> InterviewStartResponse:
        mode = (getattr(req, "mode", "standard") or "standard").lower()

        if mode == "resume":
            from app.services.resume_service import ResumeService
            resume_svc = ResumeService()
            if file_bytes:
                parsed_resume = resume_svc.parse_resume_for_interview(file_bytes, filename or "resume.pdf")
            elif getattr(req, "resume_text", None):
                parsed_resume = resume_svc.parse_resume_for_interview(req.resume_text.encode("utf-8"), "resume.txt")
            else:
                parsed_resume = {
                    "candidate_name": "Candidate",
                    "primary_technology": req.technology or "Software Engineering",
                    "skills": [req.technology or "Python"],
                    "projects": [],
                    "hr_topics": ["Teamwork", "Problem Solving"]
                }

            session = self.session_repo.create_session(
                user_id=req.user_id or "candidate_123",
                technology=parsed_resume.get("primary_technology", req.technology or "Resume-Based"),
                initial_difficulty=req.initial_difficulty or "Easy"
            )
            session.mode = "resume"
            session.resume_text = parsed_resume.get("raw_text")
            session.resume_data = parsed_resume
            self.db.commit()
            self.db.refresh(session)

            first_q = self.selection_service.select_next_resume_question(
                session_id=session.id,
                resume_data=parsed_resume,
                current_difficulty=session.current_difficulty,
                last_score=None
            )
        else:
            # Standard Mode
            session = self.session_repo.create_session(
                user_id=req.user_id or "candidate_123",
                technology=req.technology or "Python",
                initial_difficulty=req.initial_difficulty or "Easy"
            )
            session.mode = "standard"
            self.db.commit()
            self.db.refresh(session)

            first_q = self.selection_service.select_next_question(
                session_id=session.id,
                technology=session.technology,
                difficulty=session.current_difficulty
            )

        # Convert question text to speech
        audio_path = await self.audio_service.text_to_speech(first_q.question_text)
        first_q.audio_url = audio_path

        return InterviewStartResponse(
            session_id=session.id,
            user_id=session.user_id,
            technology=session.technology,
            mode=session.mode,
            status=session.status,
            current_difficulty=session.current_difficulty,
            first_question=first_q
        )

    async def submit_answer(
        self,
        session_id: str,
        question_id: Optional[str],
        generated_question_id: Optional[str],
        candidate_answer: str,
        candidate_audio_path: Optional[str] = None
    ) -> AnswerEvaluationResponse:
        session = self.session_repo.get_by_id(session_id)
        if not session or session.status == "COMPLETED":
            raise ValueError("Invalid or completed interview session.")

        # 1. Retrieve Question Context & Expected Answer
        question_text = ""
        expected_answer = ""
        target_question_id = None
        target_gen_question_id = None

        # Normalize empty strings to None
        if question_id in ("", "null", "None"):
            question_id = None
        if generated_question_id in ("", "null", "None"):
            generated_question_id = None

        # Check question_id in curated table first, then generated table
        if question_id:
            db_q = self.question_repo.get_by_id(question_id)
            if db_q:
                question_text = db_q.question
                expected_answer = db_q.expected_answer
                target_question_id = db_q.id
            else:
                gen_q = self.gen_q_repo.get_by_id(question_id)
                if gen_q:
                    question_text = gen_q.question_text
                    expected_answer = gen_q.expected_answer
                    target_gen_question_id = gen_q.id

        # Check generated_question_id if still not found
        if not question_text and generated_question_id:
            gen_q = self.gen_q_repo.get_by_id(generated_question_id)
            if gen_q:
                question_text = gen_q.question_text
                expected_answer = gen_q.expected_answer
                target_gen_question_id = gen_q.id
            else:
                db_q = self.question_repo.get_by_id(generated_question_id)
                if db_q:
                    question_text = db_q.question
                    expected_answer = db_q.expected_answer
                    target_question_id = db_q.id

        if not question_text:
            raise ValueError("Question not found for evaluation.")

        # 2. Gemini Answer Evaluation
        eval_result = self.gemini_service.evaluate_answer(
            question=question_text,
            expected_answer=expected_answer,
            candidate_answer=candidate_answer
        )

        # 3. Apply Backend State Machine Rules for Next Difficulty
        next_diff = self._determine_next_difficulty(session.current_difficulty, eval_result.score)

        # 4. Save Answer & Evaluation Record to DB
        answer_record = self.answer_repo.save_answer(
            session_id=session.id,
            question_id=target_question_id,
            generated_question_id=target_gen_question_id,
            question_text=question_text,
            expected_answer=expected_answer,
            candidate_transcript=candidate_answer,
            candidate_audio_path=candidate_audio_path,
            score=eval_result.score,
            confidence_score=eval_result.confidence_score,
            feedback=eval_result.feedback,
            fluency_feedback=eval_result.fluency_feedback,
            missing_topics=eval_result.missing_topics,
            filler_words_detected=eval_result.filler_words_detected,
            next_difficulty=next_diff
        )

        # Self-Learning Auto-Curation Loop:
        # If the question was dynamically generated by LLM and candidate scored >= 5.0, auto-promote it to permanent DB!
        if generated_question_id and eval_result.score >= 5.0:
            try:
                from app.services.learning_service import QuestionLearningService
                learning_svc = QuestionLearningService(self.db)
                learning_svc.promote_generated_question(generated_question_id)
            except Exception as le:
                logger.warning(f"Auto-promotion warning: {le}")

        # 5. Update Session State
        updated_session = self.session_repo.update_session_state(
            session_id=session.id,
            next_difficulty=next_diff,
            score_to_add=eval_result.score
        )

        # Check if interview threshold reached
        session_completed = updated_session.question_count >= self.MAX_QUESTIONS_PER_SESSION
        next_q_payload = None

        if not session_completed:
            # 6. Select Next Question (Resume vs Standard)
            if getattr(session, "mode", "standard") == "resume" and getattr(session, "resume_data", None):
                next_q_payload = self.selection_service.select_next_resume_question(
                    session_id=session.id,
                    resume_data=session.resume_data,
                    current_difficulty=next_diff,
                    last_score=eval_result.score
                )
            else:
                next_q_payload = self.selection_service.select_next_question(
                    session_id=session.id,
                    technology=session.technology,
                    difficulty=next_diff
                )
            # Synthesize TTS for next question
            audio_path = await self.audio_service.text_to_speech(next_q_payload.question_text)
            next_q_payload.audio_url = audio_path
        else:
            self.session_repo.update_session_state(session_id=session.id, next_difficulty=next_diff, score_to_add=0.0, status="COMPLETED")

        return AnswerEvaluationResponse(
            answer_id=answer_record.id,
            session_id=session.id,
            transcribed_text=candidate_answer,
            score=eval_result.score,
            confidence_score=eval_result.confidence_score,
            feedback=eval_result.feedback,
            fluency_feedback=eval_result.fluency_feedback,
            filler_words_detected=eval_result.filler_words_detected,
            missing_topics=eval_result.missing_topics,
            current_difficulty=session.current_difficulty,
            next_difficulty=next_diff,
            next_question=next_q_payload,
            session_completed=session_completed
        )

    def generate_final_report(self, session_id: str) -> FinalReportResponse:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        answers = self.answer_repo.get_answers_for_session(session_id)
        history = [
            {
                "question": a.question_text,
                "candidate_answer": a.candidate_transcript,
                "score": a.score,
                "confidence_score": getattr(a, "confidence_score", 8.0),
                "feedback": a.feedback,
                "fluency_feedback": getattr(a, "fluency_feedback", None),
                "filler_words_detected": getattr(a, "filler_words_detected", []),
                "missing_topics": a.missing_topics
            }
            for a in answers
        ]

        report_data = self.gemini_service.generate_final_report(
            technology=session.technology,
            answers_history=history
        )

        # Mark session as completed if not already
        if session.status != "COMPLETED":
            self.session_repo.update_session_state(session.id, session.current_difficulty, 0.0, status="COMPLETED")

        return FinalReportResponse(
            session_id=session.id,
            technology=session.technology,
            questions_answered=len(answers),
            technical_score=report_data.get("technical_score", 8.0),
            communication_score=report_data.get("communication_score", 8.5),
            confidence_rating=report_data.get("confidence_rating", 8.0),
            strong_topics=report_data.get("strong_topics", []),
            weak_topics=report_data.get("weak_topics", []),
            overall_feedback=report_data.get("overall_feedback", "Solid performance overall."),
            learning_roadmap=report_data.get("learning_roadmap", []),
            detailed_history=history
        )
