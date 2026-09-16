from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.schemas.resume import ResumeScreeningResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resume", tags=["Resume Screening"])
resume_service = ResumeService()

@router.post("/screen", response_model=ResumeScreeningResponse, status_code=status.HTTP_200_OK)
async def screen_resume(file: UploadFile = File(...)):
    """
    Upload a candidate resume (PDF, TXT, or DOCX) to evaluate Candidate Strengths, Weaknesses, Key Skills, Score, and Recommendations.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")
    
    filename_lower = file.filename.lower()
    allowed_extensions = (".pdf", ".txt", ".docx")
    if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.filename}'. Allowed formats: PDF (.pdf), Text (.txt), Word (.docx)"
        )
    
    contents = await file.read()
    if not contents or len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    try:
        return resume_service.screen_resume(file_bytes=contents, filename=file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the resume: {str(e)}"
        )
