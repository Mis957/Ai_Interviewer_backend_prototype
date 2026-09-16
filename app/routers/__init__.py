from app.routers.interview import router as interview_router
from app.routers.questions import router as questions_router
from app.routers.analytics import router as analytics_router
from app.routers.resume import router as resume_router

__all__ = ["interview_router", "questions_router", "analytics_router", "resume_router"]
