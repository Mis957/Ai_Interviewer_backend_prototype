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
        difficulty: str
    ) -> NextQuestionPayload:
        """
        Question Selection Logic:
        1. Search Database for matching technology and difficulty.
        2. Exclude questions already asked in this session.
        3. If suitable DB question exists -> return it.
        4. If DB question NOT found -> Call Gemini to dynamically generate question & save to DB.
        """
        # Fetch asked question IDs in this session to prevent repetition
        session_answers = self.answer_repo.get_answers_for_session(session_id)
        asked_q_ids = [a.question_id for a in session_answers if a.question_id]
        asked_topics = [a.question_text[:30] for a in session_answers]

        # Step 1: Database Search
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
                is_llm_generated=False
            )

        # Step 2: Gemini Fallback Generation
        gen_data = self.gemini_service.generate_dynamic_question(
            technology=technology,
            difficulty=difficulty,
            existing_topics=asked_topics
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
        - Determines next category ('project', 'skill', 'hr_behavioral')
        - Performs topic rotation if candidate struggled (last_score < 5.0)
        - Generates tailored question via LLM and saves to generated_questions table
        """
        session_answers = self.answer_repo.get_answers_for_session(session_id)
        asked_topics = [a.question_text[:30] for a in session_answers]
        q_count = len(session_answers)

        # Category rotation strategy
        categories = ["project", "skill", "hr_behavioral"]

        # Topic rotation rule: if last_score < 5.0 (poor answer), force category rotation so candidate doesn't get stuck
        if last_score is not None and last_score < 5.0:
            next_category = categories[(q_count + 1) % len(categories)]
            next_difficulty = "Easy"
        elif last_score is not None and last_score >= 8.0:
            next_category = categories[q_count % len(categories)]
            if current_difficulty == "Easy":
                next_difficulty = "Medium"
            elif current_difficulty == "Medium":
                next_difficulty = "Hard"
            else:
                next_difficulty = "Hard"
        else:
            next_category = categories[q_count % len(categories)]
            next_difficulty = current_difficulty

        # Fallback if no projects exist in resume data
        if next_category == "project" and not resume_data.get("projects"):
            next_category = "skill"

        # Step 1: Check Database for matching pre-curated question first
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

