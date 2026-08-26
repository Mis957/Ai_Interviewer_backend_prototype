from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.question_repo import QuestionRepository
from app.schemas.question import QuestionCreate, QuestionResponse

router = APIRouter(prefix="/questions", tags=["Question Bank Management"])

@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db)
):
    """
    Adds a new curated technical question to the Question Bank database.
    """
    try:
        repo = QuestionRepository(db)
        return repo.create_question(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[QuestionResponse])
def list_questions(
    technology: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves all curated active questions, optionally filtered by technology track.
    """
    repo = QuestionRepository(db)
    if technology:
        return repo.get_questions_by_technology(technology)
    return repo.get_all()

@router.get("/random", response_model=List[QuestionResponse])
def get_random_questions(
    technology: Optional[str] = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Retrieves a set of random questions from the Question Bank database.
    """
    repo = QuestionRepository(db)
    return repo.get_random_questions(limit=limit, technology=technology)
