import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.services.resume_service import ResumeService

logging.basicConfig(level=logging.INFO)

def test_resume():
    print("\n--- Testing Resume Screening ---")
    svc = ResumeService()
    
    sample_resume = """
    JOHN DOE
    Email: john@example.com | Phone: 123-456-7890
    
    SUMMARY:
    Senior Software Engineer with 4+ years of experience in Python, FastAPI, PostgreSQL, Docker, and REST APIs.
    
    SKILLS:
    - Python, FastAPI, Django, Flask
    - PostgreSQL, MySQL, Redis, Supabase
    - Docker, Kubernetes, CI/CD, Git
    
    EXPERIENCE:
    Backend Engineer | TechCorp (2022 - Present)
    - Architected RESTful microservices handling over 500k daily active requests using Python FastAPI.
    - Optimized SQL queries and database indexes, reducing API latency by 45%.
    - Built automated unit testing pipeline achieving 90%+ code coverage.
    """
    
    print("Screening sample resume...")
    result = svc.screen_resume(sample_resume.encode("utf-8"), "resume.txt")
    
    print("\n[SUCCESS] Resume Screening Result:")
    print("Candidate Name:", result.candidate_name)
    print("Overall Score:", result.overall_score)
    print("Key Skills:", result.key_skills)
    print("Strengths:", result.strengths)
    print("Weaknesses:", result.weaknesses)
    print("Recommendations:", result.recommendations)
    print("Suggested Technologies:", result.suggested_technologies)

if __name__ == "__main__":
    test_resume()
