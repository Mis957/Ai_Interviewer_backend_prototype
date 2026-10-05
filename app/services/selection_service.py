from typing import Tuple, Optional, List
from sqlalchemy.orm import Session
from app.repositories.question_repo import QuestionRepository, GeneratedQuestionRepository
from app.repositories.session_repo import InterviewAnswerRepository
from app.services.gemini_service import GeminiService
from app.schemas.interview import NextQuestionPayload

class QuestionSelectionService:
    def __init__(
        self,
        question_repo: QuestionRepository,
        gen_question_repo: GeneratedQuestionRepository,
        answer_repo: InterviewAnswerRepository,
        gemini_service: GeminiService
    ):
        self.question_repo = question_repo
        self.gen_question_repo = gen_question_repo
        self.answer_repo = answer_repo
        self.gemini_service = gemini_service

    def select_next_question(
        self,
        session_id: str,
        technology: str,
        difficulty: str,
        target_role: Optional[str] = None,
        years_of_experience: Optional[str] = None
    ) -> NextQuestionPayload:
        """
        Stage Flow & Adaptive Probing Selection Logic (Standard Mode):
        - Q1 (Intro Stage): 'Tell me about yourself, your technical background & experience with {technology}'
        - Q2 (Project Stage): A concrete implementation or problem-solving example in {technology}
        - Q3+ (Technical Adaptive Stage):
            * Rotates through concepts, debugging, performance, concurrency/reliability, and trade-offs
            * Lasts indefinitely until the timer expires.
            * If previous score >= 7.0: 'deep_dive' into internal mechanics/edge cases of previous topic.
            * If previous score < 5.0: 'pivot' cleanly away from weak topic to another concept.
        """
        session_answers = self.answer_repo.get_answers_for_session(session_id)
        asked_q_ids = [a.question_id for a in session_answers if a.question_id]
        asked_topics = [a.question_text for a in session_answers]
        q_count = len(session_answers) + 1

        # Determine Interview Flow Strategy:
        # - Q1 (q_count == 1): "intro" (Introductory Opener: "Tell me about yourself...")
        # - Q2 (q_count == 2): "project" (Stage 2: Real-world Project Architecture & Trade-offs)
        # - Q3+ (q_count >= 3): "technical_adaptive" (Stage 3: Core Technology Concepts & Internals)
        if q_count == 1:
            stage = "intro"
        elif q_count == 2:
            stage = "project"
        else:
            stage = "technical_adaptive"

        # Determine Adaptive Direction from previous answer
        adaptive_mode = None
        previous_topic = None
        previous_score = None

        if session_answers:
            last_ans = session_answers[-1]
            previous_score = last_ans.score
            previous_topic = getattr(last_ans, "topic", None) or last_ans.question_text[:40]

            if last_ans.score >= 7.0:
                adaptive_mode = "deep_dive"
            elif last_ans.score < 5.0:
                adaptive_mode = "pivot"

        # Step 1: Dynamic LLM Question Generation with Stage & Adaptive Rules (Primary)
        gen_data = self.gemini_service.generate_dynamic_question(
            technology=technology,
            difficulty=difficulty,
            existing_topics=asked_topics,
            target_role=target_role,
            years_of_experience=years_of_experience,
            stage=stage,
            adaptive_mode=adaptive_mode,
            previous_topic=previous_topic,
            previous_score=previous_score,
            question_sequence=max(0, q_count - 3)
        )

        if gen_data and gen_data.get("question"):
            saved_gen_q = self.gen_question_repo.save_generated_question(
                session_id=session_id,
                technology=technology,
                topic=gen_data.get("topic", f"{technology} Topic"),
                difficulty=difficulty,
                question_text=gen_data.get("question", ""),
                expected_answer=gen_data.get("expected_answer", ""),
                keywords=gen_data.get("keywords", [])
            )
            return NextQuestionPayload(
                question_id=None,
                generated_question_id=saved_gen_q.id,
                technology=saved_gen_q.technology,
                topic=saved_gen_q.topic,
                difficulty=saved_gen_q.difficulty,
                question_text=saved_gen_q.question_text,
                is_llm_generated=True,
                question_category=stage
            )

        # Step 2: Database Fallback if LLM generation was unavailable
        if stage != "intro":
            db_question = self.question_repo.find_matching_question(
                technology=technology,
                difficulty=difficulty,
                excluded_ids=asked_q_ids
            )
            if db_question:
                return NextQuestionPayload(
                    question_id=db_question.id,
                    generated_question_id=None,
                    technology=db_question.technology,
                    topic=db_question.topic,
                    difficulty=db_question.difficulty,
                    question_text=db_question.question,
                    is_llm_generated=False,
                    question_category=stage
                )

        raise RuntimeError("Failed to generate or retrieve interview question.")

    def select_next_resume_question(
        self,
        session_id: str,
        resume_data: dict,
        current_difficulty: str,
        last_score: Optional[float] = None
    ) -> NextQuestionPayload:
        """
        Adaptive Resume Question Selection Flow:
        - Phase 1: Q1 (q_count == 0) -> "intro" ("Tell me about yourself and your technical background")
        - Phase 2: Q2 to Q(1+N) -> "project" (Covering concrete implementation, challenges, and trade-offs)
        - Phase 3: Following questions -> "technology" (Core concepts for technologies mentioned,
                                                       e.g., functions/decorators in Python, indexing in SQL,
                                                       rotating through varied technical question angles)
        """
        session_answers = self.answer_repo.get_answers_for_session(session_id)
        asked_topics = [a.question_text for a in session_answers]
        q_count = len(session_answers)
        next_difficulty = current_difficulty
        if last_score is not None:
            if last_score >= 8.0:
                next_difficulty = "Hard"
            elif last_score >= 5.0:
                next_difficulty = "Medium"
            else:
                next_difficulty = "Easy"

        projects = resume_data.get("projects") or []
        skills = resume_data.get("skills") or []
        primary_tech = resume_data.get("primary_technology", "Python")

        # Include project stacks as well as listed skills so every resume technology
        # can be selected during the technical phase.
        ordered_skills = []

        def add_technology(value):
            if not isinstance(value, str):
                return
            technology = value.strip()
            if technology and technology.casefold() not in {
                existing.casefold() for existing in ordered_skills
            }:
                ordered_skills.append(technology)

        add_technology(primary_tech)
        if isinstance(skills, str):
            skills = [skills]
        for skill in skills:
            add_technology(skill)
        for project in projects:
            if not isinstance(project, dict):
                continue
            project_stack = project.get("tech_stack") or []
            if isinstance(project_stack, str):
                project_stack = [project_stack]
            for technology in project_stack:
                add_technology(technology)

        if not ordered_skills:
            ordered_skills = ["Python"]

        # Calculate project questions budget:
        # User requirement: maximum 5 questions such that all projects are covered and all questions related to them
        num_projects = len(projects)
        if num_projects == 0:
            total_project_questions = 0
        elif num_projects == 1:
            total_project_questions = 3  # Thorough coverage of the project: overview, hurdle, and trade-offs
        else:
            total_project_questions = min(5, max(num_projects, 5))  # Exactly 5 questions (max 5) covering all projects

        # 3-Phase Flow State Assignment
        if q_count == 0:
            next_category = "intro"
            target_project = None
            project_aspect = None
            target_technology = None
        elif 1 <= q_count <= total_project_questions:
            next_category = "project"
            proj_idx = q_count - 1
            target_project = projects[proj_idx % num_projects]
            if proj_idx < num_projects:
                project_aspect = "overview"  # Initial architecture & responsibilities
            else:
                round_num = proj_idx // num_projects
                if round_num == 1:
                    project_aspect = "hurdle_or_bottleneck"  # Challenges, bugs, concurrency
                else:
                    project_aspect = "tradeoffs_or_scaling"  # Engineering trade-offs and scaling
            target_technology = None
        else:
            # Phase 3: Technologies & Core Concepts (functions, decorators, generators, etc. until timer ends)
            next_category = "technology"
            tech_idx = q_count - total_project_questions - 1
            target_technology = ordered_skills[tech_idx % len(ordered_skills)]
            # Progress each technology independently as the stack rotates.
            technology_sequence = tech_idx // len(ordered_skills)
            target_project = None
            project_aspect = None

        # Step 1: LLM Dynamic Resume Question Generation (Primary)
        gen_data = self.gemini_service.generate_resume_question(
            resume_data=resume_data,
            category=next_category,
            difficulty=next_difficulty,
            existing_topics=asked_topics,
            target_project=target_project,
            project_aspect=project_aspect,
            target_technology=target_technology,
            last_score=last_score,
            question_sequence=(
                technology_sequence
                if next_category == "technology"
                else 0
            )
        )

        if gen_data and gen_data.get("question"):
            saved_gen_q = self.gen_question_repo.save_generated_question(
                session_id=session_id,
                technology=target_technology or primary_tech or "Resume-Based",
                topic=gen_data.get("topic", f"Resume {next_category.title()}"),
                difficulty=next_difficulty,
                question_text=gen_data.get("question", ""),
                expected_answer=gen_data.get("expected_answer", ""),
                keywords=gen_data.get("keywords", [])
            )
            return NextQuestionPayload(
                question_id=None,
                generated_question_id=saved_gen_q.id,
                technology=saved_gen_q.technology,
                topic=saved_gen_q.topic,
                difficulty=saved_gen_q.difficulty,
                question_text=saved_gen_q.question_text,
                is_llm_generated=True,
                question_category=next_category
            )

        # Step 2: Database Fallback if LLM is unavailable
        if next_category != "intro":
            asked_q_ids = [a.question_id for a in session_answers if a.question_id]
            primary_tech = target_technology or resume_data.get("primary_technology", "Resume-Based")
            db_question = self.question_repo.find_matching_question(
                technology=primary_tech,
                difficulty=next_difficulty,
                excluded_ids=asked_q_ids
            )
            if db_question:
                return NextQuestionPayload(
                    question_id=db_question.id,
                    generated_question_id=None,
                    technology=db_question.technology,
                    topic=db_question.topic,
                    difficulty=db_question.difficulty,
                    question_text=db_question.question,
                    is_llm_generated=False,
                    question_category=next_category
                )

        raise RuntimeError("Failed to generate or retrieve resume interview question.")
