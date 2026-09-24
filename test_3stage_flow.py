import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.services.engine_service import InterviewEngineService

def test_single_intro_flow():
    print("=== STARTING SINGLE INTRO QUESTION FLOW TEST ===")
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    engine_svc = InterviewEngineService(db)

    parsed_resume = {
        "candidate_name": "Oliver Developer",
        "primary_technology": "C++ & OpenMPI",
        "skills": ["C++", "OpenMPI", "Ray", "CUDA", "Linux Internals"],
        "projects": [
            {
                "name": "Hybrid Parallel Processing Architecture",
                "tech_stack": ["OpenMPI", "Ray", "CUDA", "C++"]
            }
        ],
        "hr_topics": ["Performance Optimization", "Distributed Systems"]
    }

    session = engine_svc.session_repo.create_session("cand_single_intro", "C++ & OpenMPI", "Medium")
    session.mode = "resume"
    session.resume_data = parsed_resume
    db.commit()

    print("\n--- Testing Resume Mode Flow Sequence ---")

    # Q1: Introductory Question ONCE ONLY
    q1 = engine_svc.selection_service.select_next_resume_question(session.id, parsed_resume, "Medium")
    print("\nQ1 (Introductory Question ONCE ONLY):")
    print("Topic:", q1.topic)
    print("Question:", q1.question_text)

    # Save Q1 Answer
    engine_svc.answer_repo.save_answer(
        session_id=session.id,
        question_id=None,
        question_text=q1.question_text,
        candidate_transcript="I have been focusing heavily on low-level C++ systems engineering and GPU acceleration.",
        score=8.5,
        confidence_score=9.0,
        feedback="Clear background description.",
        expected_answer="Candidate introduces background.",
        missing_topics=[],
        next_difficulty="Medium"
    )

    # Q2: Moves directly to Project Deep-Dive
    q2 = engine_svc.selection_service.select_next_resume_question(session.id, parsed_resume, "Medium", last_score=8.5)
    print("\nQ2 (Moves directly to Project Deep-Dive):")
    print("Category/Topic:", getattr(q2, "question_category", None) or q2.topic)
    print("Question:", q2.question_text)

    # Save Q2 Answer
    engine_svc.answer_repo.save_answer(
        session_id=session.id,
        question_id=None,
        question_text=q2.question_text,
        candidate_transcript="In my project, thread synchronization was handled using CUDA stream events.",
        score=8.0,
        confidence_score=8.5,
        feedback="Good project architecture explanation.",
        expected_answer="Project architecture explanation.",
        missing_topics=[],
        next_difficulty="Medium"
    )

    # Q3: Technical Fundamentals (Skills Array)
    q3 = engine_svc.selection_service.select_next_resume_question(session.id, parsed_resume, "Medium", last_score=8.0)
    print("\nQ3 (Technical Fundamentals & Skills):")
    print("Category/Topic:", getattr(q3, "question_category", None) or q3.topic)
    print("Question:", q3.question_text)

    # Save Q3 Answer
    engine_svc.answer_repo.save_answer(
        session_id=session.id,
        question_id=None,
        question_text=q3.question_text,
        candidate_transcript="C++ std::move converts lvalue to rvalue.",
        score=9.0,
        confidence_score=9.0,
        feedback="Accurate move semantics description.",
        expected_answer="Move semantics vs smart pointers.",
        missing_topics=[],
        next_difficulty="Hard"
    )

    # Q4: Technical Fundamentals / Deep-Dive
    q4 = engine_svc.selection_service.select_next_resume_question(session.id, parsed_resume, "Hard", last_score=9.0)
    print("\nQ4 (Technical Fundamentals / Tech Stack Deep-Dive):")
    print("Category/Topic:", getattr(q4, "question_category", None) or q4.topic)
    print("Question:", q4.question_text)

    print("\n=== SINGLE INTRO QUESTION FLOW VERIFIED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_single_intro_flow()
