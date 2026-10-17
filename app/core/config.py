import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Interview Readiness Platform Engine"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./interview_prototype.db"
    OFFLINE_DATABASE_URL: str | None = None
    
    # LM Studio Local AI
    LM_STUDIO_BASE_URL: str = "http://192.168.240.1:1234/v1"
    LM_STUDIO_MODEL: str = "meta-llama-3.1-8b-instruct"
    LM_STUDIO_API_KEY: str = "lm-studio"
    
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
    
    # Task-Specific Provider Priority Chains (comma-separated list of providers: lm_studio, groq, gemini)
    QUESTION_GEN_PROVIDERS: str = "lm_studio,groq,gemini"
    EVALUATION_PROVIDERS: str = "lm_studio,groq,gemini"
    ANALYSIS_PROVIDERS: str = "lm_studio,groq,gemini"
    
    # Storage & Audio
    AUDIO_STORAGE_DIR: str = "./audio_storage"
    USE_MOCK_SPEECH: bool = False
    WHISPER_MODEL_NAME: str = "base"
    WHISPER_MODELS_DIR: str = "./models/whisper"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure audio directory exists
os.makedirs(settings.AUDIO_STORAGE_DIR, exist_ok=True)
