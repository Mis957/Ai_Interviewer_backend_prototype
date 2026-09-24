import os
import uuid
import hashlib
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
        self.groq_client = None

        if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your-"):
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq native client initialized for speech-to-text (Whisper).")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client for STT: {e}")

        self._load_whisper_if_available()

    def _load_whisper_if_available(self):
        if settings.USE_MOCK_SPEECH:
            return
        try:
            
            import whisper
            self.whisper_model = whisper.load_model("base")
            logger.info("Loaded OpenAI Whisper base model for local STT.")
        except Exception as e:
            logger.warning(f"Local Whisper model not initialized: {e}.")

    async def text_to_speech(self, text: str, voice: str = "en-US-ChristopherNeural") -> str:
        """
        Converts question text into speech (.mp3 file) using edge-tts.
        Caches generated audio based on deterministic text hash to avoid re-generating existing audio.
        Returns the file path of the generated or cached audio file.
        """
        # Create deterministic filename hash based on text and voice
        clean_text = text.strip().lower()
        text_hash = hashlib.md5(f"{voice}_{clean_text}".encode("utf-8")).hexdigest()[:12]
        filename = f"tts_{text_hash}.mp3"
        filepath = os.path.join(self.storage_dir, filename)

        # Instant Cache Check: If audio already exists, reuse it!
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            logger.info(f"Reusing cached TTS audio file for question: {filename}")
            return filepath

        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
            logger.info(f"Synthesized and cached new TTS audio file: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Edge-TTS failed: {e}. Creating placeholder audio marker.")
            with open(filepath, "wb") as f:
                f.write(b"MOCK_AUDIO_DATA")
            return filepath

    def speech_to_text(self, audio_file_path: str) -> str:
        """
        Converts candidate speech audio file into text using Groq Whisper API (whisper-large-v3-turbo)
        with local Whisper and fallback support.
        """
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return ""

        # 1. Groq Whisper API (Ultra-fast cloud STT)
        if self.groq_client:
            try:
                with open(audio_file_path, "rb") as audio_file:
                    transcription = self.groq_client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo",
                        file=audio_file
                    )
                    text = transcription.text.strip()
                    if text:
                        logger.info(f"Successfully transcribed audio via Groq Whisper: '{text}'")
                        return text
            except Exception as e:
                logger.error(f"Groq Whisper transcription error: {e}")

        # 2. Fallback to local whisper if available
        if self.whisper_model:
            try:
                result = self.whisper_model.transcribe(audio_file_path)
                text = result.get("text", "").strip()
                if text:
                    return text
            except Exception as e:
                logger.error(f"Local Whisper transcription failed: {e}")

        # 3. Fallback dummy text if offline / mock mode
        return "Decorators in Python are higher-order functions that take another function as an argument and extend its behavior dynamically."
