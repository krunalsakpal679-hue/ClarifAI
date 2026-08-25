"""
ClarifAI Legal Text Cleaning Router
Internal endpoint for deterministic text normalization, hyphenation repair, and header stripping.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.text_cleaning import TextCleaningRequest, TextCleaningResponse
from app.services.text_cleaning_service import clean_legal_text
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Text Processing"])


@router.post(
    "/clean-text",
    response_model=TextCleaningResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def clean_text_endpoint(payload: TextCleaningRequest):
    """
    Internal endpoint to clean and normalize raw extracted legal text.
    """
    if payload.raw_text is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_INPUT",
                "message": "raw_text cannot be null."
            }
        )

    result = clean_legal_text(
        payload.raw_text,
        preserve_page_markers=payload.preserve_page_markers
    )
    return TextCleaningResponse(**result)
