import sys
import os
import logging

# Ensure root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.gemini_service import GeminiService
from app.core.config import settings

logging.basicConfig(level=logging.INFO)

def test_task_fallback_architecture():
    print("\n--- 1. Testing GeminiService Initialization ---")
    svc = GeminiService()
    print("Question Gen Providers:", svc.question_gen_providers)
    print("Evaluation Providers:", svc.evaluation_providers)
    print("Analysis Providers:", svc.analysis_providers)

    assert svc.question_gen_providers == ["groq", "groq", "gemini"], "Question Gen providers mismatch"
    assert svc.evaluation_providers == ["groq", "groq", "gemini"], "Evaluation providers mismatch"
    assert svc.analysis_providers == ["groq", "groq", "gemini"], "Analysis providers mismatch"

    print("\n--- 2. Testing Question Generation Task Execution ---")
    q_res = svc.generate_dynamic_question("Python", "Easy")
    print("Generated Question Result:")
    print("  Topic:", q_res.get("topic"))
    print("  Question:", q_res.get("question"))
    assert q_res.get("question"), "Question text should not be empty"

    print("\n--- 3. Testing Answer Evaluation Task Execution ---")
    eval_res = svc.evaluate_answer(
        question="What is a Python decorator?",
        expected_answer="A decorator wraps a function to modify its behavior dynamically.",
        candidate_answer="A decorator in Python uses @ syntax to wrap another function and extend functionality."
    )
    print("Evaluation Result:")
    print("  Score:", eval_res.score)
    print("  Confidence Score:", eval_res.confidence_score)
    print("  Feedback:", eval_res.feedback)
    assert eval_res.score >= 0.0, "Score should be non-negative"

    print("\n--- 4. Testing Final Analysis Task Execution ---")
    report_res = svc.generate_final_report(
        technology="Python",
        answers_history=[{
            "question": "What is a decorator?",
            "candidate_answer": "Wraps a function dynamically.",
            "score": 8.5,
            "feedback": "Good answer."
        }]
    )
    print("Final Report Result:")
    print("  Technical Score:", report_res.get("technical_score"))
    print("  Overall Feedback:", report_res.get("overall_feedback"))
    assert report_res.get("technical_score") is not None, "Technical score should be present"

    print("\n--- 5. Testing Complete Fallback when Providers Fail ---")
    # Simulate failed clients by overriding client objects temporarily
    old_groq = svc.groq_client
    old_gemini = svc.client
    svc.groq_client = None
    svc.client = None

    print("Simulating all APIs unavailable...")
    q_fallback = svc.generate_dynamic_question("React", "Hard")
    print("Offline Question Fallback Topic:", q_fallback.get("topic"))
    assert "React" in q_fallback.get("topic")

    eval_fallback = svc.evaluate_answer(
        question="What is React Virtual DOM?",
        expected_answer="In-memory representation of real DOM",
        candidate_answer="Virtual DOM is a lightweight copy of the DOM."
    )
    print("Offline Eval Fallback Score:", eval_fallback.score)
    assert eval_fallback.score > 0.0

    report_fallback = svc.generate_final_report("React", [])
    print("Offline Report Fallback Score:", report_fallback.get("technical_score"))
    assert report_fallback.get("technical_score") is not None

    # Restore clients
    svc.groq_client = old_groq
    svc.client = old_gemini

    print("\nALL TASK-SPECIFIC API FALLBACK TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_task_fallback_architecture()
