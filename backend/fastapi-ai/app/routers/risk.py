"""
ClarifAI Legal-BERT Clause Risk Classification Router
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.risk import ClauseRiskRequest, ClauseRiskResponse
from app.services.risk_service import classify_clause_risk
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Risk Classification"])


@router.post(
    "/classify-risk",
    response_model=ClauseRiskResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def classify_risk_endpoint(request: ClauseRiskRequest):
    """
    Internal endpoint for Stage 2 Legal-BERT clause risk classification.
    """
    if not request.clause_text.strip():
        raise HTTPException(status_code=400, detail="Clause text must not be empty.")

    result = classify_clause_risk(
        clause_text=request.clause_text,
        rule_findings=request.rule_findings
    )
    return ClauseRiskResponse(**result)
