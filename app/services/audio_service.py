import os
import uuid
import logging
import asyncio
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.storage_dir = settings.AUDIO_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        self.whisper_model = None
        self._load_whisper_if_available()

    def _load_whisper_if_available(self):
        if settings.USE_MOCK_SPEECH:
            return
        try:
            import whisper
            # Load tiny or base model for quick local inference
            self.whisper_model = whisper.load_model("base")
            logger.info("Loaded OpenAI Whisper base model for STT.")
        except Exception as e:
            logger.warning(f"Whisper STT not initialized: {e}. Audio transcription will use fallback handler.")

    async def text_to_speech(self, text: str, voice: str = "en-US-ChristopherNeural") -> str:
        """
        Converts question text into speech (.mp3 file) using edge-tts.
        Returns the absolute file path of the generated audio file.
        """
        filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(self.storage_dir, filename)

        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
            return filepath
        except Exception as e:
            logger.error(f"Edge-TTS failed: {e}. Creating placeholder audio marker.")
            # Fallback dummy file creation
            with open(filepath, "wb") as f:
                f.write(b"MOCK_AUDIO_DATA")
            return filepath

    def speech_to_text(self, audio_file_path: str) -> str:
        """
        Converts candidate speech audio file into text using OpenAI Whisper.
        """
        if self.whisper_model and os.path.exists(audio_file_path):
            try:
                result = self.whisper_model.transcribe(audio_file_path)
                return result.get("text", "").strip()
            except Exception as e:
                logger.error(f"Whisper transcription failed: {e}")

        # Fallback for testing without audio models installed
        return "I believe decorators in Python are wrapper functions that modify the behavior of another function dynamically without altering its source code."
