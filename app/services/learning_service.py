import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models.question import Question, GeneratedQuestion
from app.models.session import InterviewAnswer, InterviewSession

logger = logging.getLogger(__name__)

class QuestionLearningService:
    def __init__(self, db: Session):
        self.db = db

    def promote_generated_question(self, generated_question_id: str) -> bool:
        """
        Promotes an LLM-generated question into the permanent curated Question Bank database.
        """
        gen_q = self.db.query(GeneratedQuestion).filter(GeneratedQuestion.id == generated_question_id).first()
        if not gen_q:
            return False

        # Check if identical question already exists in main database
        existing = self.db.query(Question).filter(Question.question == gen_q.question_text).first()
        if existing:
            return False

        new_question = Question(
            technology=gen_q.technology,
            topic=gen_q.topic,
            difficulty=gen_q.difficulty,
            question=gen_q.question_text,
            expected_answer=gen_q.expected_answer,
            keywords=gen_q.keywords or [],
            llm_generated=True,
            active=True
        )
        self.db.add(new_question)
        self.db.commit()
        logger.info(f"Auto-promoted generated question '{gen_q.topic}' into permanent Question Bank.")
        return True

    def get_learning_analytics(self) -> Dict[str, Any]:
        """
        Calculates backend self-learning insights:
        - Total curated questions vs LLM-learned questions.
        - Topic performance averages and mastery ratings.
        """
        total_questions = self.db.query(Question).count()
        learned_questions = self.db.query(Question).filter(Question.llm_generated == True).count()
        total_sessions = self.db.query(InterviewSession).count()
        completed_sessions = self.db.query(InterviewSession).filter(InterviewSession.status == "COMPLETED").count()
        
        # Calculate topic performance breakdown
        answers = self.db.query(InterviewAnswer).all()
        topic_scores = {}
        for ans in answers:
            # Extract main topic identifier from question
            topic = ans.question_text.split(":")[0][:25] if ":" in ans.question_text else ans.question_text[:25]
            if topic not in topic_scores:
                topic_scores[topic] = {"total_score": 0.0, "count": 0}
            topic_scores[topic]["total_score"] += ans.score
            topic_scores[topic]["count"] += 1

        topic_breakdown = [
            {
                "topic": t,
                "average_score": round(data["total_score"] / data["count"], 1),
                "total_attempts": data["count"]
            }
            for t, data in topic_scores.items()
        ]

        learned_list = self.db.query(Question).filter(Question.llm_generated == True).all()
        learned_qs = [
            {
                "id": q.id,
                "technology": q.technology,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "question": q.question,
                "created_at": q.created_at.isoformat()
            }
            for q in learned_list
        ]

        return {
            "total_questions_in_bank": total_questions,
            "auto_learned_questions_count": learned_questions,
            "total_sessions_conducted": total_sessions,
            "completed_sessions": completed_sessions,
            "topic_analytics": topic_breakdown,
            "auto_curated_questions": learned_qs
        }
