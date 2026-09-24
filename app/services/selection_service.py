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
        Stage Flow & Adaptive Probing Selection Logic:
        - Q1 (Intro Stage): 'Tell me about yourself, your technical background & recent projects'
        - Q2 (Project Stage): Applied project engineering, architecture decisions & trade-offs
        - Q3-Q5 (Technical Adaptive Stage):
            * If previous score >= 7.0: 'deep_dive' into internal mechanics/edge cases of previous topic.
            * If previous score < 5.0: 'pivot' cleanly away from weak topic to another concept.
        """
        session_answers = self.answer_repo.get_answers_for_session(session_id)
        asked_q_ids = [a.question_id for a in session_answers if a.question_id]
        asked_topics = [a.question_text[:40] for a in session_answers]
        q_count = len(session_answers) + 1

        # Determine Interview Flow Strategy:
        # - Q1 (q_count == 1): "intro" (Basic Introductory Opener ONCE ONLY: "Walk me through your background...")
        # - Q2 (q_count == 2): "project" (Stage 2: Project Architecture Deep-Dive & Trade-offs)
        # - Q3-Q5 (q_count >= 3): "technical_adaptive" (Stage 3: Technical Fundamentals & Tech Stack)
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

        # Step 1: Database Search (Bypassed for Q1 Intro to generate live dynamic interviewer opener)
        if stage != "intro":
            db_question = self.question_repo.find_matching_question(
                technology=technology,
                difficulty=difficulty,
                excluded_ids=asked_q_ids
            )

            if db_question and adaptive_mode != "deep_dive":
                return NextQuestionPayload(
                    question_id=db_question.id,
                    generated_question_id=None,
                    technology=db_question.technology,
                    topic=db_question.topic,
                    difficulty=db_question.difficulty,
                    question_text=db_question.question,
                    is_llm_generated=False
                )

        # Step 2: Dynamic LLM Question Generation with Stage & Adaptive Rules
        gen_data = self.gemini_service.generate_dynamic_question(
            technology=technology,
            difficulty=difficulty,
            existing_topics=asked_topics,
            target_role=target_role,
            years_of_experience=years_of_experience,
            stage=stage,
            adaptive_mode=adaptive_mode,
            previous_topic=previous_topic,
            previous_score=previous_score
        )

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
            is_llm_generated=True
        )

    def select_next_resume_question(
        self,
        session_id: str,
        resume_data: dict,
        current_difficulty: str,
        last_score: Optional[float] = None
    ) -> NextQuestionPayload:
        """
        Adaptive Resume Question Selection:
        - Q1 (q_count == 0): 'intro' (Introductory question ONCE ONLY)
        - Q2 (q_count == 1): 'project' (Flagship project deep-dive)
        - Q3+ (q_count >= 2): 'skill' (Technical fundamentals pulled from parsed_skills)
        """
        session_answers = self.answer_repo.get_answers_for_session(session_id)
        asked_topics = [a.question_text[:30] for a in session_answers]
        q_count = len(session_answers)

        # Interview Flow Strategy (Resume Mode):
        # Q1 (q_count == 0) -> "intro" (Basic Introductory Opener ONCE ONLY)
        # Q2 (q_count == 1) -> "project" (Flagship Project Deep-Dive)
        # Q3-Q5 (q_count >= 2) -> "skill" (Technical Fundamentals & parsed_skills)
        if q_count == 0:
            next_category = "intro"
            next_difficulty = current_difficulty
        elif q_count == 1:
            next_category = "project"
            next_difficulty = current_difficulty
        else:
            next_category = "skill"
            if last_score is not None and last_score < 5.0:
                next_difficulty = "Easy"
            elif last_score is not None and last_score >= 8.0:
                next_difficulty = "Hard" if current_difficulty == "Medium" else "Medium"
            else:
                next_difficulty = current_difficulty

        # Fallback if no projects exist in resume data
        if next_category == "project" and not resume_data.get("projects"):
            next_category = "skill"

        # Step 1: Check Database for matching pre-curated question (Bypassed for Q1 Intro)
        if next_category != "intro":
            asked_q_ids = [a.question_id for a in session_answers if a.question_id]
            primary_tech = resume_data.get("primary_technology", "Resume-Based")
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

        # Step 2: LLM Dynamic Generation if not found in DB
        gen_data = self.gemini_service.generate_resume_question(
            resume_data=resume_data,
            category=next_category,
            difficulty=next_difficulty,
            existing_topics=asked_topics
        )

        saved_gen_q = self.gen_question_repo.save_generated_question(
            session_id=session_id,
            technology="Resume-Based",
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

