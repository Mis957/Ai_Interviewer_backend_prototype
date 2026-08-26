import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine, Base
from app.routers import interview_router, questions_router, analytics_router

# Ensure tables are created on startup (for SQLite/Dev mode)
Base.metadata.create_all(bind=engine)

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
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": settings.DATABASE_URL.split(":")[0],
        "storage": settings.AUDIO_STORAGE_DIR
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
