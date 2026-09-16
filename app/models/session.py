import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, default="candidate_demo")
    technology = Column(String(50), nullable=False)
    current_difficulty = Column(String(20), nullable=False, default="Easy")
    status = Column(String(20), nullable=False, default="STARTED")  # STARTED, IN_PROGRESS, COMPLETED
    total_score = Column(Float, default=0.0)
    question_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")
    generated_questions = relationship("GeneratedQuestion", back_populates="session", cascade="all, delete-orphan")


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    generated_question_id = Column(String, ForeignKey("generated_questions.id", ondelete="SET NULL"), nullable=True)
    
    question_text = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=False)
    candidate_transcript = Column(Text, nullable=True)
    candidate_audio_path = Column(String, nullable=True)
    
    score = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=True, default=8.0)
    feedback = Column(Text, nullable=True)
    fluency_feedback = Column(Text, nullable=True)
    missing_topics = Column(JSON, nullable=True, default=list)
    filler_words_detected = Column(JSON, nullable=True, default=list)
    next_difficulty = Column(String(20), nullable=False)
    evaluated_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("InterviewSession", back_populates="answers")
