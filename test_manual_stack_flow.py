import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import Base
from app.models.question import Question
from app.services.engine_service import InterviewEngineService

logging.basicConfig(level=logging.INFO)

def test_manual_tech_stack_selection():
    print("=== STARTING MANUAL TECH STACK SELECTION TEST ===")
    
    # 1. Setup in-memory SQLite DB and seed questions for Python & DBMS
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed 2 questions for Python and 1 for DBMS
    q_py1 = Question(
        technology="Python",
        topic="Decorators",
        difficulty="Easy",
        question="What is a decorator in Python?",
        expected_answer="A wrapper function.",
        keywords=["function", "wrapper"],
        active=True
    )
    q_py2 = Question(
        technology="Python",
        topic="AsyncIO",
        difficulty="Medium",
        question="Explain Python AsyncIO event loop.",
        expected_answer="Cooperative multitasking loop.",
        keywords=["event loop", "async"],
        active=True
    )
    db.add(q_py1)
    db.add(q_py2)
    db.commit()

    engine_svc = InterviewEngineService(db)

    # Create manual setup session for Python
    session = engine_svc.session_repo.create_session("cand_manual_py", "Python", "Easy")
    session.mode = "standard"
    db.commit()

    # Retrieval #1: Should retrieve q_py1 from database table!
    q1 = engine_svc.selection_service.select_next_question(
        session_id=session.id,
        technology="Python",
        difficulty="Easy"
    )
    print(f"\n[Retrieval 1 - Table Match] is_llm_generated: {q1.is_llm_generated}")
    print(f"Question ID: {q1.question_id}")
    print(f"Question Text: {q1.question_text}")
    assert q1.is_llm_generated is False, "First question should be retrieved from DB table"
    assert q1.question_id == q_py1.id, "Should match seeded Python decorator question"

    # Save answer for Q1 to mark question_id as asked
    engine_svc.answer_repo.save_answer(
        session_id=session.id,
        question_id=q1.question_id,
        question_text=q1.question_text,
        candidate_transcript="A decorator wraps another function.",
        score=8.0,
        confidence_score=8.5,
        feedback="Good description.",
        expected_answer="Wrapper function.",
        missing_topics=[],
        next_difficulty="Medium"
    )

    # Retrieval #2: Should retrieve q_py2 from database table (fallback match for Medium)!
    q2 = engine_svc.selection_service.select_next_question(
        session_id=session.id,
        technology="Python",
        difficulty="Medium"
    )
    print(f"\n[Retrieval 2 - Table Match] is_llm_generated: {q2.is_llm_generated}")
    print(f"Question ID: {q2.question_id}")
    print(f"Question Text: {q2.question_text}")
    assert q2.is_llm_generated is False, "Second question should also be retrieved from DB table"
    assert q2.question_id == q_py2.id, "Should match seeded Python AsyncIO question"

    # Save answer for Q2 to mark question_id as asked
    engine_svc.answer_repo.save_answer(
        session_id=session.id,
        question_id=q2.question_id,
        question_text=q2.question_text,
        candidate_transcript="AsyncIO runs cooperative event loop.",
        score=8.5,
        confidence_score=9.0,
        feedback="Good AsyncIO answer.",
        expected_answer="Event loop.",
        missing_topics=[],
        next_difficulty="Hard"
    )

    # Retrieval #3: Table questions for Python are now EXHAUSTED.
    # Should fall back to dynamic LLM question generation strictly focused ONLY on Python!
    q3 = engine_svc.selection_service.select_next_question(
        session_id=session.id,
        technology="Python",
        difficulty="Hard"
    )
    print(f"\n[Retrieval 3 - Dynamic Generation Fallback] is_llm_generated: {q3.is_llm_generated}")
    print(f"Generated Q ID: {q3.generated_question_id}")
    print(f"Question Text: {q3.question_text}")
    assert q3.is_llm_generated is True, "Third question should be dynamically generated via LLM"
    assert q3.question_text, "Generated question text must not be empty"

    print("\n=== MANUAL TECH STACK SELECTION TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_manual_tech_stack_selection()
