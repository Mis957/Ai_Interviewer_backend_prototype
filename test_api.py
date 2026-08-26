import requests

BASE_URL = "http://127.0.0.1:8000"

def test_full_interview_flow():
    print("--- 1. Testing GET /health ---")
    h_res = requests.get(f"{BASE_URL}/health")
    print(f"Health Response ({h_res.status_code}):", h_res.json())

    print("\n--- 2. Testing POST /interview/start ---")
    start_payload = {
        "user_id": "demo_candidate_42",
        "technology": "Python",
        "initial_difficulty": "Easy"
    }
    start_res = requests.post(f"{BASE_URL}/interview/start", json=start_payload)
    print(f"Start Response ({start_res.status_code}):")
    data = start_res.json()
    print("Session ID:", data.get("session_id"))
    print("First Question:", data.get("first_question"))

    session_id = data.get("session_id")
    first_q = data.get("first_question", {})
    q_id = first_q.get("question_id")
    gen_q_id = first_q.get("generated_question_id")

    print("\n--- 3. Testing POST /interview/answer ---")
    answer_payload = {
        "session_id": session_id,
        "question_id": q_id,
        "generated_question_id": gen_q_id,
        "candidate_answer": "A decorator in Python is a design pattern used to wrap a function to extend its behavior dynamically using @decorator syntax."
    }
    ans_res = requests.post(f"{BASE_URL}/interview/answer", data=answer_payload)
    print(f"Answer Response ({ans_res.status_code}):")
    ans_data = ans_res.json()
    print("Score:", ans_data.get("score"))
    print("Feedback:", ans_data.get("feedback"))
    print("Next Difficulty:", ans_data.get("next_difficulty"))
    print("Next Question:", ans_data.get("next_question"))

    print("\n--- 4. Testing POST /interview/end ---")
    end_res = requests.post(f"{BASE_URL}/interview/end", data={"session_id": session_id})
    print(f"End Response ({end_res.status_code}):")
    end_data = end_res.json()
    print("Technical Score:", end_data.get("technical_score"))
    print("Communication Score:", end_data.get("communication_score"))
    print("Learning Roadmap:", end_data.get("learning_roadmap"))

if __name__ == "__main__":
    test_full_interview_flow()
