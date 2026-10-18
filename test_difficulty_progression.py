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

def test_score_based_difficulty_progression():
    print("=== STARTING SCORE-BASED DIFFICULTY PROGRESSION TEST ===")
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed Python questions for Easy, Medium, and Hard
    q_easy = Question(technology="Python", topic="Basic Syntax", difficulty="Easy", question="Easy Python Q", expected_answer="Ans Easy", active=True)
    q_med = Question(technology="Python", topic="Decorators", difficulty="Medium", question="Medium Python Q", expected_answer="Ans Med", active=True)
    q_hard = Question(technology="Python", topic="Memory Management", difficulty="Hard", question="Hard Python Q", expected_answer="Ans Hard", active=True)
    
    db.add_all([q_easy, q_med, q_hard])
    db.commit()

    engine_svc = InterviewEngineService(db)

    # 1. Test _determine_next_difficulty unit logic
    assert engine_svc._determine_next_difficulty("Easy", 8.5) == "Medium", "Score >= 8 on Easy should escalate to Medium"
    assert engine_svc._determine_next_difficulty("Medium", 9.0) == "Hard", "Score >= 8 on Medium should escalate to Hard"
    assert engine_svc._determine_next_difficulty("Hard", 8.5) == "Hard", "Score >= 8 on Hard should stay at max Hard"
    assert engine_svc._determine_next_difficulty("Hard", 4.0) == "Medium", "Score < 5 on Hard should de-escalate to Medium"
    assert engine_svc._determine_next_difficulty("Medium", 3.0) == "Easy", "Score < 5 on Medium should de-escalate to Easy"
    assert engine_svc._determine_next_difficulty("Easy", 4.0) == "Easy", "Score < 5 on Easy should stay at min Easy"
    assert engine_svc._determine_next_difficulty("Medium", 6.5) == "Medium", "Score between 5 and 8 should stay same"
    
    print("[Pass] Engine difficulty escalation & de-escalation rules intact!")

    # 2. Test End-to-End Session progression with table & dynamic fallback
    session = engine_svc.session_repo.create_session("cand_diff_test", "Python", "Easy")
    session.mode = "standard"
    db.commit()

    # Q1 (Initial difficulty: Easy)
    q1 = engine_svc.selection_service.select_next_question(session.id, "Python", session.current_difficulty)
    print(f"Q1 Requested Diff: Easy | Retrived Q: '{q1.question_text}' | Retrived Diff: {q1.difficulty}")
    assert q1.difficulty == "Easy", "Q1 should be Easy"

    # Candidate scores 8.5 on Q1 (High Score) -> next difficulty should become "Medium"
    next_d1 = engine_svc._determine_next_difficulty(session.current_difficulty, 8.5)
    engine_svc.session_repo.update_session_state(session.id, next_difficulty=next_d1, score_to_add=8.5)
    session = engine_svc.session_repo.get_by_id(session.id)
    assert session.current_difficulty == "Medium", "Session difficulty should escalate to Medium after 8.5 score"

    # Q2 (Current difficulty: Medium)
    q2 = engine_svc.selection_service.select_next_question(session.id, "Python", session.current_difficulty)
    print(f"Q2 Requested Diff: Medium | Retrived Q: '{q2.question_text}' | Retrived Diff: {q2.difficulty}")
    assert q2.difficulty == "Medium", "Q2 should be Medium"

    # Candidate scores 9.0 on Q2 (High Score) -> next difficulty should become "Hard"
    next_d2 = engine_svc._determine_next_difficulty(session.current_difficulty, 9.0)
    engine_svc.session_repo.update_session_state(session.id, next_difficulty=next_d2, score_to_add=9.0)
    session = engine_svc.session_repo.get_by_id(session.id)
    assert session.current_difficulty == "Hard", "Session difficulty should escalate to Hard after 9.0 score"

    # Q3 (Current difficulty: Hard)
    q3 = engine_svc.selection_service.select_next_question(session.id, "Python", session.current_difficulty)
    print(f"Q3 Requested Diff: Hard | Retrived Q: '{q3.question_text}' | Retrived Diff: {q3.difficulty}")
    assert q3.difficulty == "Hard", "Q3 should be Hard"

    # Candidate struggles with 3.0 on Q3 (Low Score) -> next difficulty should de-escalate to "Medium"
    next_d3 = engine_svc._determine_next_difficulty(session.current_difficulty, 3.0)
    engine_svc.session_repo.update_session_state(session.id, next_difficulty=next_d3, score_to_add=3.0)
    session = engine_svc.session_repo.get_by_id(session.id)
    assert session.current_difficulty == "Medium", "Session difficulty should de-escalate to Medium after 3.0 score"

    print("\n=== SCORE-BASED DIFFICULTY PROGRESSION TEST PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_score_based_difficulty_progression()
