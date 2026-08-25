"""
FastAPI Router for Pairwise Document Clause Comparison Service (AI-PHASE-COMPARISON)
"""

import logging
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional

from app.core.config import settings
from app.models.comparison import ComparisonRequest, ComparisonResponse
from app.services.comparison_service import compare_documents

logger = logging.getLogger(__name__)

comparison_router = APIRouter(prefix="/api/v1/comparison", tags=["Pairwise Document Comparison"])


def verify_internal_secret(x_internal_service_secret: Optional[str] = Header(None)) -> None:
    expected_secret = settings.INTERNAL_SERVICE_SECRET
    if expected_secret:
        if not x_internal_service_secret or x_internal_service_secret != expected_secret:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Invalid or missing internal service secret header."
            )


@comparison_router.post(
    "/compare-documents",
    response_model=ComparisonResponse,
    summary="Compare two contract documents clause-by-clause",
    description="Performs embedding similarity matching and generates grounded difference explanations for changed pairs."
)
async def compare_documents_endpoint(
    req: ComparisonRequest,
    _: None = Depends(verify_internal_secret)
) -> ComparisonResponse:
    try:
        res = compare_documents(
            user_id=req.user_id,
            document_id_a=req.document_id_a,
            document_id_b=req.document_id_b,
            matched_threshold=req.matched_threshold,
            changed_threshold=req.changed_threshold
        )
        return ComparisonResponse(**res)
    except ValueError as val_err:
        logger.warning(f"Comparison Request Error: {val_err}")
        raise HTTPException(
            status_code=422,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.error(f"Internal error during document comparison: {exc}")
        raise HTTPException(
            status_code=500,
            detail="AI processing is temporarily unavailable. Please try again later. (COMPARISON_FAILURE)"
        )
