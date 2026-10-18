import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.services.gemini_service import GeminiService

logging.basicConfig(level=logging.INFO)

def test_qwen_hf_local():
    print("\n--- Testing Qwen2.5-1.5B-Instruct Local HuggingFace Model ---")
    svc = GeminiService()
    
    prompt = "Generate 1 easy interview question for Python regarding decorators."
    print(f"Sending prompt to HuggingFace model ({svc.hf_model_id})...")
    
    try:
        response = svc._call_huggingface_local(prompt)
        print("\n[SUCCESS] Model Output:")
        print(response)
    except Exception as e:
        print(f"\n[ERROR] Failed to run model: {e}")

if __name__ == "__main__":
    test_qwen_hf_local()
