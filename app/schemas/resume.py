from typing import List, Optional
from pydantic import BaseModel, Field

class ResumeScreeningResponse(BaseModel):
    candidate_name: Optional[str] = Field(default="Candidate", description="Name extracted from resume if available")
    overall_score: float = Field(..., description="Overall resume quality score from 0.0 to 100.0")
    strengths: List[str] = Field(..., description="List of key candidate strengths identified in the resume")
    weaknesses: List[str] = Field(..., description="List of candidate weaknesses or areas for improvement")
    key_skills: List[str] = Field(default_factory=list, description="Extracted technical and soft skills")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations to enhance resume and readiness")
    suggested_technologies: List[str] = Field(default_factory=list, description="Recommended technology tracks for practice")
