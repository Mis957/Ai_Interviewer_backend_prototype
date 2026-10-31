import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.services.engine_service import InterviewEngineService
from seed_data import INITIAL_QUESTIONS
from app.models.question import Question

def test_resume_flow_complete():
    print("=== TESTING RESUME FLOW WITH 3 PHASES ===")
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed curated questions into the test database
    for q_data in INITIAL_QUESTIONS:
        db.add(Question(
            technology=q_data["technology"],
            topic=q_data["topic"],
            difficulty=q_data["difficulty"],
            question=q_data["question"],
            expected_answer=q_data["expected_answer"],
            keywords=q_data["keywords"],
            active=True
        ))
    db.commit()

    engine_svc = InterviewEngineService(db)

    # Candidate resume with 2 projects and technologies (Python, SQL, Docker)
    parsed_resume = {
        "candidate_name": "Sarah Connor",
        "primary_technology": "Python",
        "skills": ["Python", "SQL", "Docker", "FastAPI"],
        "projects": [
            {
                "name": "E-Commerce Microservices Engine",
                "tech_stack": ["Python", "FastAPI", "Docker", "SQL"],
                "description": "High-throughput asynchronous order processing and inventory service."
            },
            {
                "name": "Real-time Telemetry Analytics Pipeline",
                "tech_stack": ["Python", "SQL", "Redis"],
                "description": "Streaming event ingestion pipeline with automated anomaly detection."
            }
        ],
        "hr_topics": ["Problem Solving", "System Architecture Trade-offs"]
    }

    session = engine_svc.session_repo.create_session("sarah_101", "Python", "Medium")
    session.mode = "resume"
    session.resume_data = parsed_resume
    db.commit()

    # -------------------------------------------------------------
    # PHASE 1: "Tell me about yourself" (Question 1)
    # -------------------------------------------------------------
    q1 = engine_svc.selection_service.select_next_resume_question(session.id, parsed_resume, "Medium")
    print("\n--- PHASE 1: Introduction ---")
    print(f"Q1 [{q1.question_category}]: {q1.question_text}")
    assert q1.question_category == "intro"
    assert any(w in q1.question_text.lower() for w in ["tell me about yourself", "yourself", "background", "introduce", "technical area", "engineering"])

    engine_svc.answer_repo.save_answer(
        session_id=session.id,
        question_id=None,
        question_text=q1.question_text,
        candidate_transcript="I am a software engineer with 3 years of experience specializing in backend Python services and distributed pipelines.",
        score=8.5,
        confidence_score=9.0,
        feedback="Clear and confident introduction.",
        expected_answer="Candidate introduces background.",
        missing_topics=[],
        next_difficulty="Medium"
    )

    # -------------------------------------------------------------
    # PHASE 2: Projects from Resume (Max 5 Questions Covering All Projects)
    # Candidate has 2 projects:
    # Q2 -> Project 1
    # Q3 -> Project 2
    # Q4 -> Project 1 hurdle
    # Q5 -> Project 2 hurdle
    # Q6 -> Project trade-offs / scaling (Total = 5 project questions)
    # -------------------------------------------------------------
    print("\n--- PHASE 2: Projects (Covering All Resume Projects, Max 5 Questions) ---")
    project_questions = []
    
    for i in range(2, 7):
        q = engine_svc.selection_service.select_next_resume_question(session.id, parsed_resume, "Medium", last_score=8.0)
        print(f"Q{i} [{q.question_category} - {q.topic}]: {q.question_text}")
        assert q.question_category == "project"
        project_questions.append(q)

        engine_svc.answer_repo.save_answer(
            session_id=session.id,
            question_id=None,
            question_text=q.question_text,
            candidate_transcript="In this project, we designed asynchronous workers and structured database connections to handle peak loads.",
            score=8.0,
            confidence_score=8.5,
            feedback="Good architectural explanation.",
            expected_answer="Project architecture explanation.",
            missing_topics=[],
            next_difficulty="Medium"
        )

    assert len(project_questions) == 5, f"Expected 5 project questions, got {len(project_questions)}"
    
    # Verify both projects were covered in the questions/topics
    all_proj_text = " ".join([q.question_text + " " + q.topic for q in project_questions]).lower()
    assert "e-commerce" in all_proj_text or "microservices" in all_proj_text or "order" in all_proj_text, "Project 1 should be covered"
    assert "telemetry" in all_proj_text or "analytics" in all_proj_text or "pipeline" in all_proj_text or "event" in all_proj_text, "Project 2 should be covered"

    # -------------------------------------------------------------
    # PHASE 3: Technologies Mentioned in Resume (Lasts Until Timer is Over)
    # E.g. Python (functions, decorators, generators, GIL), SQL (indexes, ACID), etc.
    # Questions continue dynamically: Q7, Q8, Q9, Q10...
    # -------------------------------------------------------------
    print("\n--- PHASE 3: Technologies Mentioned (Continues until timer is over) ---")
    tech_questions = []

    for i in range(7, 11):
        q = engine_svc.selection_service.select_next_resume_question(session.id, parsed_resume, "Medium", last_score=8.0)
        print(f"Q{i} [{q.question_category} - {q.topic}]: {q.question_text}")
        assert q.question_category == "technology"
        tech_questions.append(q)

        engine_svc.answer_repo.save_answer(
            session_id=session.id,
            question_id=q.question_id,
            question_text=q.question_text,
            candidate_transcript="In Python, decorators are higher order functions that wrap other functions, and generators use yield to save memory.",
            score=8.5,
            confidence_score=9.0,
            feedback="Solid technical grasp.",
            expected_answer="Technical explanation.",
            missing_topics=[],
            next_difficulty="Hard"
        )

    assert len(tech_questions) == 4, f"Expected 4 technology questions, got {len(tech_questions)}"

    print("\n=== RESUME FLOW VERIFIED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_resume_flow_complete()

