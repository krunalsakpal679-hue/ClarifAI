"""
ClarifAI Plain-Language Clause Simplification Router (AI-PHASE-SIMPLIFICATION)
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.simplification import SimplificationRequest, SimplificationResponse
from app.services.simplification_service import simplify_document_clauses
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Simplification"])


@router.post(
    "/simplify-clauses",
    response_model=SimplificationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def simplify_clauses_endpoint(request: SimplificationRequest):
    """
    Internal endpoint for per-clause plain-language simplification and why-flagged explanation.
    """
    if request.clauses is None:
        raise HTTPException(status_code=400, detail="Clauses list cannot be null.")

    result = simplify_document_clauses(
        clauses=request.clauses,
        rule_findings=request.rule_findings
    )
    return SimplificationResponse(**result)
