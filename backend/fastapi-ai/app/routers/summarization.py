"""
ClarifAI BART Automated Summarization Router (AI-PHASE-SUMMARY)
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.summarization import (
    SummarizationRequest,
    SummarizationResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse
)
from app.services.summarization_service import summarize_text, generate_document_summary
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Summarization"])


@router.post(
    "/summarize",
    response_model=SummarizationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def summarize_endpoint(request: SummarizationRequest):
    """
    Internal endpoint for BART-base automated single section text summarization.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text for summarization must not be empty.")

    result = summarize_text(
        text=request.text,
        max_length=request.max_length or 200,
        min_length=request.min_length or 30
    )
    return SummarizationResponse(**result)


@router.post(
    "/summarize-document",
    response_model=DocumentSummaryResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def summarize_document_endpoint(request: DocumentSummaryRequest):
    """
    Internal endpoint for 4-field executive document summarization with failure isolation (Chapter 16.4).
    """
    if request.clauses is None:
        raise HTTPException(status_code=400, detail="Clauses list cannot be null.")

    result = generate_document_summary(
        clauses=request.clauses,
        rule_findings=request.rule_findings
    )
    return DocumentSummaryResponse(**result)
