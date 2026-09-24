import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Interview Readiness Platform Engine"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./interview_prototype.db"  # Fallback to local SQLite if postgres not configured
    
    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    
    # Groq AI Keys
    GROQ_API_KEY: str = ""
    GROQ_API_KEY_SECONDARY: str = ""
    GROQ_QUESTION_GEN_API_KEY: str = ""
    GROQ_EVALUATION_API_KEY: str = ""
    GROQ_ANALYSIS_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    
    # Task-Specific Provider Priority Chains (comma-separated list of providers: groq, gemini)
    QUESTION_GEN_PROVIDERS: str = "groq,groq,gemini"
    EVALUATION_PROVIDERS: str = "groq,groq,gemini"
    ANALYSIS_PROVIDERS: str = "groq,groq,gemini"
    
    # Storage & Audio
    AUDIO_STORAGE_DIR: str = "./audio_storage"
    USE_MOCK_SPEECH: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure audio directory exists
os.makedirs(settings.AUDIO_STORAGE_DIR, exist_ok=True)
