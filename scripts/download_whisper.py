"""
Utility script to download OpenAI Whisper models for offline use.
Usage:
    python scripts/download_whisper.py [model_name]
Example:
    python scripts/download_whisper.py base
    python scripts/download_whisper.py tiny
    python scripts/download_whisper.py small
"""

import sys
import os
import whisper

DEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "whisper"))
os.makedirs(DEST_DIR, exist_ok=True)

model_name = sys.argv[1] if len(sys.argv) > 1 else "base"

if model_name not in whisper._MODELS:
    print(f"Error: Unknown model '{model_name}'. Available models: {list(whisper._MODELS.keys())}")
    sys.exit(1)

target_path = os.path.join(DEST_DIR, f"{model_name}.pt")
if os.path.exists(target_path):
    print(f"Model '{model_name}' already exists offline at: {target_path} ({os.path.getsize(target_path)} bytes)")
    sys.exit(0)

print(f"Downloading Whisper model '{model_name}' to offline directory: {DEST_DIR} ...")
url = whisper._MODELS[model_name]
whisper._download(url, DEST_DIR, in_memory=False)
print(f"Successfully downloaded '{model_name}.pt' to {target_path}!")
