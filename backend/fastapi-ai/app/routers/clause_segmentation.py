"""
ClarifAI Legal Clause Segmentation Router
Internal endpoint for turning cleaned document text into an ordered list of verbatim clause records.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.clause_segmentation import ClauseSegmentationRequest, ClauseSegmentationResponse
from app.services.clause_segmentation_service import segment_document_clauses
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Clause Processing"])


@router.post(
    "/segment-clauses",
    response_model=ClauseSegmentationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def segment_clauses_endpoint(payload: ClauseSegmentationRequest):
    """
    Internal endpoint to segment cleaned document text into verbatim legal clauses.
    """
    if payload.text is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_INPUT",
                "message": "Text field cannot be null."
            }
        )

    result = segment_document_clauses(
        payload.text,
        pages=payload.pages
    )
    return ClauseSegmentationResponse(**result)
