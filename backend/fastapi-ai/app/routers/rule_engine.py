"""
ClarifAI Legal Risk Rule Engine Router
Internal endpoint for evaluating all 14 legal risk rules (R001–R014).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.rule_engine import RuleEngineRequest, RuleEngineResponse
from app.services.rule_engine_service import evaluate_rules
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Rule Engine"])


@router.post(
    "/evaluate-rules",
    response_model=RuleEngineResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def evaluate_rules_endpoint(payload: RuleEngineRequest):
    """
    Internal endpoint to evaluate document text or clauses against the 14 approved rules (R001-R014).
    Produces structured evidence findings without assigning any final severity value.
    """
    if payload.clauses is None and payload.text is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_INPUT",
                "message": "Either 'clauses' list or 'text' string must be provided."
            }
        )

    result = evaluate_rules(
        clauses=payload.clauses,
        text=payload.text
    )
    return RuleEngineResponse(**result)
