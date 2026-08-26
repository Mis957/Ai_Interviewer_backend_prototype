from typing import Optional
from pydantic import BaseModel

class STTResponse(BaseModel):
    transcription: str
    language: Optional[str] = "en"
    duration_seconds: Optional[float] = None

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-ChristopherNeural"

class TTSResponse(BaseModel):
    audio_path: str
    audio_url: str
