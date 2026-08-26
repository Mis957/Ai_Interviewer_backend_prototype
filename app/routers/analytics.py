from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.learning_service import QuestionLearningService

router = APIRouter(prefix="/analytics", tags=["Backend Self-Learning & Analytics"])

@router.get("/learning")
def get_learning_analytics(db: Session = Depends(get_db)):
    """
    Returns analytics on backend self-learning:
    - Auto-promoted generated questions count
    - Total curated questions in bank
    - Aggregate topic performance ratings
    """
    try:
        svc = QuestionLearningService(db)
        return svc.get_learning_analytics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/promote/{generated_question_id}")
def promote_question(generated_question_id: str, db: Session = Depends(get_db)):
    """
    Manually promotes an LLM-generated question into the permanent Question Bank.
    """
    try:
        svc = QuestionLearningService(db)
        success = svc.promote_generated_question(generated_question_id)
        if not success:
            raise HTTPException(status_code=400, detail="Question already promoted or invalid ID.")
        return {"status": "success", "message": "Question successfully promoted to Question Bank."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
