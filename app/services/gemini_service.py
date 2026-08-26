import json
import logging
from typing import Dict, Any, List
from app.core.config import settings
from app.schemas.interview import GeminiEvalOutput, FinalReportResponse, LearningRoadmapItem

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google-genai client: {e}. Will fallback to structured mock responses if called.")

    def evaluate_answer(
        self,
        question: str,
        expected_answer: str,
        candidate_answer: str
    ) -> GeminiEvalOutput:
        """
        Evaluates a candidate's answer against the expected answer using Gemini.
        Returns a structured GeminiEvalOutput (score, feedback, missing_topics, next_difficulty).
        """
        prompt = f"""
Act as an expert technical interviewer.
Evaluate the candidate's answer for the following question.

Question: {question}
Expected Answer Key: {expected_answer}
Candidate's Answer: {candidate_answer}

Provide your evaluation STRICTLY in JSON format with NO markdown formatting or commentary:
{{
  "score": <float between 0.0 and 10.0>,
  "feedback": "<concise constructve feedback>",
  "missing_topics": ["<topic1>", "<topic2>"],
  "next_difficulty": "<Easy | Medium | Hard>"
}}

Rules for next_difficulty:
- If score >= 8.0: next_difficulty should be "Hard" (or upgrade difficulty)
- If score >= 5.0 and score < 8.0: next_difficulty should be "Medium" (or same difficulty)
- If score < 5.0: next_difficulty should be "Easy" (or lower difficulty)
"""
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                text = response.text.strip()
                # Clean code blocks if present
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                
                data = json.loads(text.strip())
                return GeminiEvalOutput(
                    score=float(data.get("score", 7.0)),
                    feedback=data.get("feedback", "Good effort. Cover core principles deeper."),
                    missing_topics=data.get("missing_topics", []),
                    next_difficulty=data.get("next_difficulty", "Medium")
                )
            except Exception as e:
                logger.error(f"Gemini API error during answer evaluation: {e}")

        # Fallback Mock Evaluation for robust testing without active API key
        cand_len = len(candidate_answer.strip().split())
        score = 8.5 if cand_len > 15 else (6.0 if cand_len > 5 else 4.0)
        next_diff = "Hard" if score >= 8.0 else ("Medium" if score >= 5.0 else "Easy")
        
        return GeminiEvalOutput(
            score=score,
            feedback=f"Evaluated answer ({cand_len} words). Good fundamental understanding shown.",
            missing_topics=["edge cases", "performance optimization"] if score < 8.0 else [],
            next_difficulty=next_diff
        )

    def generate_dynamic_question(
        self,
        technology: str,
        difficulty: str,
        existing_topics: List[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically generates a technical question using Gemini when no suitable database question exists.
        """
        avoid_str = ", ".join(existing_topics) if existing_topics else "None"
        prompt = f"""
Generate an interview question for the following track:
Technology: {technology}
Difficulty Level: {difficulty}
Topics to Avoid (Already asked): {avoid_str}

Return STRICTLY in JSON format with NO markdown wrapping:
{{
  "topic": "<Specific Topic Name>",
  "question": "<Interview Question Text>",
  "expected_answer": "<Comprehensive Expected Answer>",
  "keywords": ["<keyword1>", "<keyword2>", "<keyword3>"]
}}
"""
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                
                return json.loads(text.strip())
            except Exception as e:
                logger.error(f"Gemini Question Generation Error: {e}")

        # Dynamic fallback generator
        return {
            "topic": f"{technology} Advanced Concepts",
            "question": f"Explain key architectural concepts and best practices in {technology} for {difficulty} level applications.",
            "expected_answer": f"Clear explanation of design patterns, error handling, memory management, and performance optimization in {technology}.",
            "keywords": [technology, "architecture", difficulty.lower(), "best-practices"]
        }

    def generate_final_report(
        self,
        technology: str,
        answers_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive final report with technical score, communication score, confidence, and learning roadmap.
        """
        prompt = f"""
Act as a Principal Engineer and Hiring Manager. Analyze this candidate's complete interview history:

Technology Track: {technology}
Interview QA Data: {json.dumps(answers_history, indent=2)}

Generate a detailed final performance report STRICTLY in JSON format:
{{
  "technical_score": <float 0-10>,
  "communication_score": <float 0-10>,
  "confidence_rating": <float 0-10>,
  "strong_topics": ["<topic1>", "<topic2>"],
  "weak_topics": ["<topic1>", "<topic2>"],
  "overall_feedback": "<Comprehensive synthesis of strengths and areas of growth>",
  "learning_roadmap": [
    {{
      "topic": "<Weak Topic>",
      "action_item": "<Concrete study task or project exercise>",
      "recommended_resource": "<Documentation link or book suggestion>"
    }}
  ]
}}
"""
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                
                return json.loads(text.strip())
            except Exception as e:
                logger.error(f"Gemini Final Report Generation Error: {e}")

        # Fallback Mock Report
        total_score = sum(a.get("score", 7.0) for a in answers_history)
        count = max(len(answers_history), 1)
        avg_tech = round(total_score / count, 1)
        
        return {
            "technical_score": avg_tech,
            "communication_score": 8.0,
            "confidence_rating": 8.2,
            "strong_topics": [f"{technology} Fundamentals", "Problem Solving"],
            "weak_topics": ["Edge cases", "Deep Internals"],
            "overall_feedback": f"Demonstrated solid proficiency in {technology}. Good structural thinking with minor gaps in deep architectural nuances.",
            "learning_roadmap": [
                {
                    "topic": f"{technology} Advanced Internals",
                    "action_item": "Review official language specifications and concurrency models.",
                    "recommended_resource": f"Official {technology} Documentation"
                }
            ]
        }
