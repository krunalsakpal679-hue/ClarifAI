"""
ClarifAI BART Automated Summarization Router
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.summarization import SummarizationRequest, SummarizationResponse
from app.services.summarization_service import summarize_text
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Summarization"])


@router.post(
    "/summarize",
    response_model=SummarizationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def summarize_endpoint(request: SummarizationRequest):
    """
    Internal endpoint for BART-base automated document and clause summarization.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text for summarization must not be empty.")

    result = summarize_text(
        text=request.text,
        max_length=request.max_length or 200,
        min_length=request.min_length or 30
    )
    return SummarizationResponse(**result)
