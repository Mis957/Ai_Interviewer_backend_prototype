from types import SimpleNamespace

from app.services.gemini_service import GeminiService
from app.services.selection_service import QuestionSelectionService


class FakeAnswerRepository:
    def __init__(self, answer_count):
        self.answers = [
            SimpleNamespace(question_id=None, question_text=f"Answered question {i}")
            for i in range(answer_count)
        ]

    def get_answers_for_session(self, session_id):
        return self.answers


class FakeGeneratedQuestionRepository:
    def save_generated_question(self, **question):
        return SimpleNamespace(id="generated-id", **question)


class FakeQuestionRepository:
    pass


class FakeGeminiService:
    def __init__(self):
        self.calls = []

    def generate_resume_question(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "topic": kwargs.get("target_technology") or "Project",
            "question": f"Question about {kwargs.get('target_technology') or 'the project'}",
            "expected_answer": "",
            "keywords": [],
        }


def make_service(answer_count):
    gemini_service = FakeGeminiService()
    service = QuestionSelectionService(
        question_repo=FakeQuestionRepository(),
        gen_question_repo=FakeGeneratedQuestionRepository(),
        answer_repo=FakeAnswerRepository(answer_count),
        gemini_service=gemini_service,
    )
    return service, gemini_service


def test_resume_transitions_to_tech_stack_after_five_project_questions():
    service, gemini_service = make_service(answer_count=6)  # Intro + 5 project answers
    resume = {
        "primary_technology": "Python",
        "skills": ["Python"],
        "projects": [
            {"name": "Log Aggregation System", "tech_stack": ["Python", "Kafka", "PostgreSQL"]},
            {"name": "Monitoring Dashboard", "tech_stack": ["React", "PostgreSQL"]},
        ],
    }

    question = service.select_next_resume_question(
        "session-id", resume, "Medium"
    )

    assert question.question_category == "technology"
    assert gemini_service.calls[-1]["target_technology"] == "Python"


def test_resume_technical_questions_include_technologies_from_project_stacks():
    service, gemini_service = make_service(answer_count=7)
    resume = {
        "primary_technology": "Python",
        "skills": ["Python"],
        "projects": [
            {"name": "Log Aggregation System", "tech_stack": ["Python", "Kafka", "PostgreSQL"]},
            {"name": "Monitoring Dashboard", "tech_stack": ["React", "PostgreSQL"]},
        ],
    }

    service.select_next_resume_question("session-id", resume, "Medium")

    assert gemini_service.calls[-1]["target_technology"] == "Kafka"


def test_each_resume_technology_progresses_and_difficulty_follows_latest_score():
    resume = {
        "primary_technology": "Python",
        "skills": ["Python", "SQL"],
        "projects": [],
    }

    for answer_count, score, expected_sequence, expected_difficulty in (
        (1, 4.0, 0, "Easy"),
        (3, 6.0, 1, "Medium"),
        (5, 8.5, 2, "Hard"),
        (7, 3.5, 3, "Easy"),
        (9, 9.0, 4, "Hard"),
    ):
        service, gemini_service = make_service(answer_count=answer_count)
        service.select_next_resume_question(
            "session-id", resume, "Medium", last_score=score
        )
        call = gemini_service.calls[-1]

        assert call["target_technology"] == "Python"
        assert call["question_sequence"] == expected_sequence
        assert call["difficulty"] == expected_difficulty
        assert call["last_score"] == score


def test_project_phase_also_uses_latest_answer_score():
    resume = {
        "primary_technology": "Python",
        "skills": ["Python"],
        "projects": [{"name": "Log Aggregation System", "tech_stack": ["Python"]}],
    }

    for score, expected_difficulty in (
        (4.0, "Easy"),
        (6.0, "Medium"),
        (9.0, "Hard"),
    ):
        service, gemini_service = make_service(answer_count=1)
        question = service.select_next_resume_question(
            "session-id", resume, "Medium", last_score=score
        )

        assert question.question_category == "project"
        assert gemini_service.calls[-1]["difficulty"] == expected_difficulty
        assert gemini_service.calls[-1]["last_score"] == score


def test_python_resume_prompt_teaches_oop_before_decorators():
    service = GeminiService.__new__(GeminiService)
    prompts = []

    def capture_prompt(task_type, prompt, system_prompt=None):
        prompts.append(prompt)
        return '{"topic":"Python","question":"How do classes work?","expected_answer":"Classes define objects.","keywords":["classes"]}'

    service._call_llm_for_task = capture_prompt
    resume = {"candidate_name": "Candidate", "skills": ["Python"], "projects": []}

    service.generate_resume_question(
        resume, "technology", "Easy", target_technology="Python",
        question_sequence=0, last_score=4.0
    )
    service.generate_resume_question(
        resume, "technology", "Medium", target_technology="Python",
        question_sequence=1, last_score=6.0
    )
    service.generate_resume_question(
        resume, "technology", "Hard", target_technology="Python",
        question_sequence=2, last_score=9.0
    )

    assert "Python fundamentals" in prompts[0]
    assert "scored 4.0/10" in prompts[0]
    assert "easier and more foundational" in prompts[0]
    assert "object-oriented" in prompts[1]
    assert "scored 6.0/10" in prompts[1]
    assert "decorators" in prompts[2]
    assert "scored 9.0/10" in prompts[2]
    assert "deeper follow-up" in prompts[2]


def test_offline_python_questions_also_progress_from_basics_to_decorators():
    service = GeminiService.__new__(GeminiService)
    service._call_llm_for_task = lambda *args, **kwargs: ""
    resume = {"candidate_name": "Candidate", "skills": ["Python"], "projects": []}

    questions = []
    for sequence in range(3):
        question = service.generate_resume_question(
            resume_data=resume,
            category="technology",
            difficulty=("Easy" if sequence < 2 else "Medium"),
            existing_topics=[item["question"] for item in questions],
            target_technology="Python",
            question_sequence=sequence,
            last_score=8.5,
        )
        questions.append(question)

    assert questions[0]["topic"] == "Python Fundamentals"
    assert questions[1]["topic"] == "Object-Oriented Programming"
    assert questions[2]["topic"] == "Decorators in Python"


def test_low_score_fallback_returns_to_foundational_python_topic():
    service = GeminiService.__new__(GeminiService)
    service._call_llm_for_task = lambda *args, **kwargs: ""
    resume = {"candidate_name": "Candidate", "skills": ["Python"], "projects": []}

    question = service.generate_resume_question(
        resume_data=resume,
        category="technology",
        difficulty="Easy",
        existing_topics=["In Python, how does asyncio schedule coroutines?"],
        target_technology="Python",
        question_sequence=4,
        last_score=3.0,
    )

    assert question["topic"] == "Python Fundamentals"
