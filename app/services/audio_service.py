import os
import sys
import uuid
import hashlib
import logging
import asyncio
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure ffmpeg binary is in PATH for local Whisper
def _ensure_ffmpeg_path():
    candidates = []
    # 1. Virtualenv Scripts directory
    venv_scripts = os.path.dirname(sys.executable)
    candidates.append(venv_scripts)

    # 2. Project root directory
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    candidates.append(project_dir)

    # 3. imageio_ffmpeg bundled binary directory if available
    try:
        import imageio_ffmpeg
        img_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if img_ffmpeg and os.path.exists(img_ffmpeg):
            candidates.append(os.path.dirname(img_ffmpeg))
    except Exception:
        pass

    curr_path = os.environ.get("PATH", "")
    for c in candidates:
        if c and os.path.exists(c) and c not in curr_path:
            curr_path = c + os.pathsep + curr_path

    os.environ["PATH"] = curr_path

_ensure_ffmpeg_path()


class AudioService:
    _cached_whisper_model = None

    def __init__(self):
        self.storage_dir = settings.AUDIO_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        self.groq_client = None

        if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your-"):
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq native client initialized for speech-to-text (Whisper).")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client for STT: {e}")

        self._load_whisper_if_available()

    @property
    def whisper_model(self):
        return AudioService._cached_whisper_model

    def _load_whisper_if_available(self):
        if settings.USE_MOCK_SPEECH:
            return
        if AudioService._cached_whisper_model is not None:
            return
        try:
            _ensure_ffmpeg_path()
            import whisper
            model_name = getattr(settings, "WHISPER_MODEL_NAME", "base")
            models_dir = getattr(settings, "WHISPER_MODELS_DIR", "./models/whisper")
            os.makedirs(models_dir, exist_ok=True)
            local_model_file = os.path.join(models_dir, f"{model_name}.pt")

            if os.path.isfile(local_model_file):
                logger.info(f"Loading local offline Whisper model from: {local_model_file}")
                AudioService._cached_whisper_model = whisper.load_model(local_model_file)
            else:
                logger.info(f"Loading Whisper model '{model_name}' (directory: '{models_dir}')")
                AudioService._cached_whisper_model = whisper.load_model(model_name, download_root=models_dir)
            logger.info("Loaded OpenAI Whisper model for local offline STT.")
        except Exception as e:
            logger.warning(f"Local Whisper model not initialized: {e}.")

    async def text_to_speech(self, text: str, voice: str = "en-US-ChristopherNeural") -> str:
        """
        Converts question text into speech (.mp3 file) using edge-tts.
        Caches generated audio based on deterministic text hash to avoid re-generating existing audio.
        Returns the file path of the generated or cached audio file.
        """
        clean_text = text.strip().lower()
        text_hash = hashlib.md5(f"{voice}_{clean_text}".encode("utf-8")).hexdigest()[:12]
        filename = f"tts_{text_hash}.mp3"
        filepath = os.path.join(self.storage_dir, filename)

        # Instant Cache Check: Only reuse if file exists and has valid audio size (> 500 bytes)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 500:
            logger.info(f"Reusing cached TTS audio file for question: {filename}")
            return filepath

        # Try Edge-TTS with retry
        for attempt in range(3):
            try:
                import edge_tts
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(filepath)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 500:
                    logger.info(f"Synthesized and cached new TTS audio file: {filename}")
                    return filepath
            except Exception as e:
                logger.warning(f"Edge-TTS attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(0.5)

        logger.warning(f"Edge-TTS generation failed for text: '{text[:50]}...'. Returning empty audio path.")
        # If generation failed, remove any partial corrupt file so it can retry later
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return ""

    def speech_to_text(self, audio_file_path: str) -> str:
        """
        Converts candidate speech audio file into text using Groq Whisper API (whisper-large-v3-turbo)
        with local Whisper and fallback support.
        """
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return ""

        file_size = os.path.getsize(audio_file_path)
        if file_size < 200:
            logger.warning(f"Audio file {audio_file_path} is too small ({file_size} bytes). No speech audio captured.")
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
                _ensure_ffmpeg_path()
                result = self.whisper_model.transcribe(audio_file_path, fp16=False)
                text = result.get("text", "").strip()
                if text:
                    logger.info(f"Successfully transcribed audio via local Whisper: '{text}'")
                    return text
            except Exception as e:
                logger.error(f"Local Whisper transcription failed: {e}")

        # No speech recognized or transcription failed
        logger.warning(f"No speech recognized for audio file: {audio_file_path}")
        return ""
