import os
import sys
from fastapi.testclient import TestClient
from app.main import app

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "test_audio")
client = TestClient(app)

def test_audio_evaluation_flow():
    print("==================================================", flush=True)
    print("  AUDIO ANSWER EVALUATION TEST SUITE (FastAPI)   ", flush=True)
    print("==================================================\n", flush=True)

    # 1. Start Session
    print("--- 1. Starting Interview Session ---", flush=True)
    start_payload = {
        "user_id": "candidate_audio_test",
        "technology": "Python",
        "initial_difficulty": "Easy"
    }
    response = client.post("/interview/start", json=start_payload)
    if response.status_code != 201:
        print(f"[FAIL] Failed to start session: {response.text}", flush=True)
        return

    data = response.json()
    session_id = data["session_id"]
    first_q = data["first_question"]
    q_id = first_q.get("question_id")
    gen_q_id = first_q.get("generated_question_id")

    print(f"[OK] Session Created: {session_id}", flush=True)
    print(f"     Question: {first_q['question_text']}", flush=True)
    print(f"     Question ID: {q_id} | Gen Question ID: {gen_q_id}\n", flush=True)

    # 2. Test Audio Files
    audio_files_to_test = [
        ("python_decorator_excellent.mp3", "Python Decorators (Fluent / Clear Delivery)"),
        ("python_decorator_hesitant_fillers.mp3", "Python Decorators (Hesitant / Filler Words & Humming)")
    ]

    for filename, label in audio_files_to_test:
        audio_path = os.path.join(AUDIO_DIR, filename)
        if not os.path.exists(audio_path):
            print(f"[SKIP] Audio file not found: {audio_path}", flush=True)
            continue

        print(f"--- 2. Testing Audio Upload: {label} ({filename}) ---", flush=True)
        form_data = {
            "session_id": session_id,
        }
        if q_id:
            form_data["question_id"] = q_id
        if gen_q_id:
            form_data["generated_question_id"] = gen_q_id

        with open(audio_path, "rb") as f:
            files = {
                "audio_file": (filename, f, "audio/mpeg")
            }
            eval_resp = client.post("/interview/evaluate-audio", data=form_data, files=files)

        if eval_resp.status_code == 200:
            eval_data = eval_resp.json()
            print("[OK] Audio Evaluated Successfully!", flush=True)
            print(f"     Technical Score: {eval_data.get('score')} / 10", flush=True)
            print(f"     Confidence Score: {eval_data.get('confidence_score')} / 10", flush=True)
            print(f"     Transcribed Text (Groq Whisper): \"{eval_data.get('transcribed_text')}\"", flush=True)
            print(f"     Technical Feedback: {eval_data.get('feedback')}", flush=True)
            print(f"     Speech Fluency Feedback: {eval_data.get('fluency_feedback')}", flush=True)
            print(f"     Filler Words Detected: {eval_data.get('filler_words_detected')}", flush=True)
            print(f"     Updated Difficulty: {eval_data.get('next_difficulty')}", flush=True)
            if eval_data.get("next_question"):
                print(f"     Next Question: {eval_data['next_question']['question_text']}", flush=True)
                # Update question IDs for next turn
                q_id = eval_data['next_question'].get("question_id")
                gen_q_id = eval_data['next_question'].get("generated_question_id")
            print("-" * 50 + "\n", flush=True)
        else:
            print(f"[FAIL] Audio Evaluation Failed ({eval_resp.status_code}): {eval_resp.text}\n", flush=True)

if __name__ == "__main__":
    test_audio_evaluation_flow()
