from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.session import InterviewSession, InterviewAnswer

class InterviewSessionRepository(BaseRepository[InterviewSession]):
    def __init__(self, db: Session):
        super().__init__(InterviewSession, db)

    def create_session(self, user_id: str, technology: str, initial_difficulty: str = "Easy") -> InterviewSession:
        session = InterviewSession(
            user_id=user_id,
            technology=technology,
            current_difficulty=initial_difficulty,
            status="STARTED",
            total_score=0.0,
            question_count=0
        )
        return self.add(session)

    def update_session_state(
        self,
        session_id: str,
        next_difficulty: str,
        score_to_add: float,
        status: Optional[str] = None
    ) -> Optional[InterviewSession]:
        session = self.get_by_id(session_id)
        if not session:
            return None

        session.current_difficulty = next_difficulty
        session.total_score += score_to_add
        session.question_count += 1
        session.updated_at = datetime.utcnow()
        if status:
            session.status = status
            
        self.db.commit()
        self.db.refresh(session)
        return session


class InterviewAnswerRepository(BaseRepository[InterviewAnswer]):
    def __init__(self, db: Session):
        super().__init__(InterviewAnswer, db)

    def save_answer(
        self,
        session_id: str,
        question_text: str,
        expected_answer: str,
        candidate_transcript: str,
        score: float,
        feedback: str,
        missing_topics: List[str],
        next_difficulty: str,
        question_id: Optional[str] = None,
        generated_question_id: Optional[str] = None,
        candidate_audio_path: Optional[str] = None
    ) -> InterviewAnswer:
        answer = InterviewAnswer(
            session_id=session_id,
            question_id=question_id,
            generated_question_id=generated_question_id,
            question_text=question_text,
            expected_answer=expected_answer,
            candidate_transcript=candidate_transcript,
            candidate_audio_path=candidate_audio_path,
            score=score,
            feedback=feedback,
            missing_topics=missing_topics,
            next_difficulty=next_difficulty
        )
        return self.add(answer)

    def get_answers_for_session(self, session_id: str) -> List[InterviewAnswer]:
        return self.db.query(InterviewAnswer).filter(InterviewAnswer.session_id == session_id).order_by(InterviewAnswer.evaluated_at.asc()).all()
