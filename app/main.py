import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import (
    get_active_engine,
    initialize_database_schema,
    is_using_offline_database,
)
from app.routers import interview_router, questions_router, analytics_router, resume_router

initialize_database_schema(get_active_engine())

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Deterministic AI Interview Engine Backend with Clean Architecture & Gemini Evaluation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated audio files as static files
os.makedirs(settings.AUDIO_STORAGE_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=settings.AUDIO_STORAGE_DIR), name="audio")

# Register API Routers
app.include_router(interview_router)
app.include_router(questions_router)
app.include_router(analytics_router)
app.include_router(resume_router)

@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to AI Interview Readiness Platform Engine API",
        "documentation": "/docs",
        "health": "/health",
        "analytics": "/analytics/learning"
    }

@app.get("/health", tags=["System"])
def health_check():
    active_engine = get_active_engine()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": "local_supabase" if is_using_offline_database() else active_engine.dialect.name,
        "offline_database": is_using_offline_database(),
        "storage": settings.AUDIO_STORAGE_DIR
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
