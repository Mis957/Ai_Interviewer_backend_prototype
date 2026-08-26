from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class QuestionBase(BaseModel):
    technology: str = Field(..., example="Python")
    topic: str = Field(..., example="Decorators")
    difficulty: str = Field(..., example="Medium")
    question: str = Field(..., example="What is a decorator in Python and how does it work?")
    expected_answer: str = Field(..., example="A function that takes another function as an argument and extends its behavior without modifying it.")
    keywords: List[str] = Field(default_factory=list, example=["higher-order function", "wrapper", "closures"])
    active: bool = True

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: str
    llm_generated: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GeneratedQuestionResponse(BaseModel):
    id: str
    session_id: str
    technology: str
    topic: str
    difficulty: str
    question_text: str
    expected_answer: str
    keywords: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
