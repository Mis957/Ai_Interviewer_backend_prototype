import sys
import tempfile
import types
import unittest
import wave
from unittest.mock import patch

from app.services.audio_service import AudioService


class AudioServiceOfflineTTSTest(unittest.IsolatedAsyncioTestCase):
    async def test_text_to_speech_falls_back_to_offline_wav(self):
        class FakeEdgeCommunicate:
            def __init__(self, text, voice):
                pass

            async def save(self, filepath):
                raise OSError("network unavailable")

        class FakeSpeechEngine:
            def save_to_file(self, text, filepath):
                with wave.open(filepath, "wb") as audio_file:
                    audio_file.setnchannels(1)
                    audio_file.setsampwidth(2)
                    audio_file.setframerate(16000)
                    audio_file.writeframes(b"\x00\x00" * 1000)

            def runAndWait(self):
                pass

        with tempfile.TemporaryDirectory() as storage_dir:
            fake_modules = {
                "edge_tts": types.SimpleNamespace(Communicate=FakeEdgeCommunicate),
                "pyttsx3": types.SimpleNamespace(init=lambda: FakeSpeechEngine()),
                "pythoncom": types.SimpleNamespace(
                    CoInitialize=lambda: None,
                    CoUninitialize=lambda: None,
                ),
            }
            with patch.dict(sys.modules, fake_modules):
                service = AudioService.__new__(AudioService)
                service.storage_dir = storage_dir

                audio_path = await service.text_to_speech("A sample question")

            self.assertTrue(audio_path.endswith(".wav"))
            with wave.open(audio_path, "rb") as audio_file:
                self.assertEqual(audio_file.getnframes(), 1000)


if __name__ == "__main__":
    unittest.main()
