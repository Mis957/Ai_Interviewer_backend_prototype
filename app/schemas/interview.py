from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class InterviewStartRequest(BaseModel):
    user_id: Optional[str] = Field("candidate_123", description="Candidate ID")
    technology: str = Field("Python", description="Technology track (Python, Java, DBMS, etc.)")
    mode: str = Field("standard", description="Interview mode: standard or resume")
    initial_difficulty: str = Field("Easy", description="Initial question difficulty")
    resume_text: Optional[str] = Field(None, description="Optional raw resume text for resume-based mode")

class NextQuestionPayload(BaseModel):
    question_id: Optional[str] = None
    generated_question_id: Optional[str] = None
    technology: str
    topic: str
    difficulty: str
    question_text: str
    audio_url: Optional[str] = None
    is_llm_generated: bool = False
    question_category: Optional[str] = Field(None, description="Category: project | skill | hr_behavioral | technical")

class InterviewStartResponse(BaseModel):
    session_id: str
    user_id: str
    technology: str
    mode: str = Field("standard", description="standard or resume")
    status: str
    current_difficulty: str
    first_question: NextQuestionPayload

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: Optional[str] = None
    generated_question_id: Optional[str] = None
    candidate_answer: str = Field(..., description="Transcribed text or directly typed answer")

class GeminiEvalOutput(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0, description="Evaluation score 0-10")
    confidence_score: float = Field(default=8.0, ge=0.0, le=10.0, description="Speech fluency & confidence score 0-10")
    feedback: str = Field(..., description="Qualitative technical evaluation feedback")
    fluency_feedback: Optional[str] = Field(default=None, description="Analysis of speech rate, pauses, humming, and filler words")
    filler_words_detected: List[str] = Field(default_factory=list, description="Detected filler words (um, uh, like, etc.)")
    missing_topics: List[str] = Field(default_factory=list, description="Topics/concepts missed by candidate")
    next_difficulty: str = Field(..., description="Recommended difficulty for next question")

class AnswerEvaluationResponse(BaseModel):
    answer_id: str
    session_id: str
    transcribed_text: Optional[str] = None
    score: float
    confidence_score: float = 8.0
    feedback: str
    fluency_feedback: Optional[str] = None
    filler_words_detected: List[str] = Field(default_factory=list)
    missing_topics: List[str]
    current_difficulty: str
    next_difficulty: str
    next_question: Optional[NextQuestionPayload] = None
    session_completed: bool = False

class LearningRoadmapItem(BaseModel):
    topic: str
    action_item: str
    recommended_resource: Optional[str] = None

class FinalReportResponse(BaseModel):
    session_id: str
    technology: str
    questions_answered: int
    technical_score: float
    communication_score: float
    confidence_rating: float
    strong_topics: List[str]
    weak_topics: List[str]
    overall_feedback: str
    learning_roadmap: List[LearningRoadmapItem]
    detailed_history: List[Dict[str, Any]]
