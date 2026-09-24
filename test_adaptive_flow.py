import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.gemini_service import GeminiService

logging.basicConfig(level=logging.INFO)

def test_adaptive_interviewer_flow():
    svc = GeminiService()

    print("\n--- 1. Testing Stage 1: Intro Opener ---")
    q1 = svc.generate_dynamic_question(
        technology="Python",
        difficulty="Easy",
        stage="intro"
    )
    print("Q1 Topic:", q1.get("topic"))
    print("Q1 Question:", q1.get("question"))
    assert "Candidate Introduction" in q1.get("topic") or "introduce" in q1.get("question").lower() or "background" in q1.get("question").lower()

    print("\n--- 2. Testing Stage 2: Project Architecture ---")
    q2 = svc.generate_dynamic_question(
        technology="Python",
        difficulty="Easy",
        stage="project"
    )
    print("Q2 Topic:", q2.get("topic"))
    print("Q2 Question:", q2.get("question"))
    assert q2.get("question"), "Q2 question text should not be empty"

    print("\n--- 3. Testing Adaptive Deep-Dive (High Score >= 7.0) ---")
    q3_deep = svc.generate_dynamic_question(
        technology="Python",
        difficulty="Medium",
        stage="technical_adaptive",
        adaptive_mode="deep_dive",
        previous_topic="Arrays & Dynamic Allocation",
        previous_score=8.5
    )
    print("Q3 Deep-Dive Topic:", q3_deep.get("topic"))
    print("Q3 Deep-Dive Question:", q3_deep.get("question"))
    assert q3_deep.get("question"), "Deep-dive question should be generated"

    print("\n--- 4. Testing Adaptive Pivot (Low Score < 5.0) ---")
    q4_pivot = svc.generate_dynamic_question(
        technology="Python",
        difficulty="Easy",
        stage="technical_adaptive",
        adaptive_mode="pivot",
        previous_topic="Stack Overflow & Recursion Limits",
        previous_score=3.5
    )
    print("Q4 Pivot Topic:", q4_pivot.get("topic"))
    print("Q4 Pivot Question:", q4_pivot.get("question"))
    assert q4_pivot.get("question"), "Pivot question should be generated"

    print("\nALL ADAPTIVE INTERVIEWER FLOW TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_adaptive_interviewer_flow()
