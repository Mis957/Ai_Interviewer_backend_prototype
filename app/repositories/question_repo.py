from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.repositories.base import BaseRepository
from app.models.question import Question, GeneratedQuestion
from app.schemas.question import QuestionCreate

class QuestionRepository(BaseRepository[Question]):
    def __init__(self, db: Session):
        super().__init__(Question, db)

    def find_matching_question(
        self,
        technology: str,
        difficulty: str,
        excluded_ids: List[str] = None
    ) -> Optional[Question]:
        """
        Finds an active question matching technology and difficulty that hasn't been asked yet in the current session.
        """
        query = self.db.query(Question).filter(
            Question.technology.ilike(technology),
            Question.difficulty.ilike(difficulty),
            Question.active == True
        )
        if excluded_ids:
            query = query.filter(Question.id.not_in(excluded_ids))
        
        # Pick one at random from candidates
        return query.order_by(func.random()).first()

    def get_questions_by_technology(self, technology: str) -> List[Question]:
        return self.db.query(Question).filter(Question.technology.ilike(technology), Question.active == True).all()

    def get_random_questions(self, limit: int = 10, technology: Optional[str] = None) -> List[Question]:
        query = self.db.query(Question).filter(Question.active == True)
        if technology:
            query = query.filter(Question.technology.ilike(technology))
        return query.order_by(func.random()).limit(limit).all()

    def create_question(self, question_in: QuestionCreate) -> Question:
        question = Question(
            technology=question_in.technology,
            topic=question_in.topic,
            difficulty=question_in.difficulty,
            question=question_in.question,
            expected_answer=question_in.expected_answer,
            keywords=question_in.keywords,
            active=question_in.active,
            llm_generated=False
        )
        return self.add(question)


class GeneratedQuestionRepository(BaseRepository[GeneratedQuestion]):
    def __init__(self, db: Session):
        super().__init__(GeneratedQuestion, db)

    def save_generated_question(
        self,
        session_id: str,
        technology: str,
        topic: str,
        difficulty: str,
        question_text: str,
        expected_answer: str,
        keywords: List[str]
    ) -> GeneratedQuestion:
        gen_q = GeneratedQuestion(
            session_id=session_id,
            technology=technology,
            topic=topic,
            difficulty=difficulty,
            question_text=question_text,
            expected_answer=expected_answer,
            keywords=keywords
        )
        return self.add(gen_q)
