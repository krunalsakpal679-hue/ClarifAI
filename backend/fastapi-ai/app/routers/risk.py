"""
ClarifAI Legal-BERT Clause Risk Classification & Output Validation Router
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.risk import (
    ClauseRiskRequest,
    ClauseRiskResponse,
    DocumentRiskRequest,
    DocumentRiskResponse,
    OutputValidationRequest,
    OutputValidationResponse
)
from app.services.risk_service import classify_clause_risk, classify_document_clauses_risk
from app.services.output_validator_service import validate_and_resolve_clause_risk
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Risk Classification"])


@router.post(
    "/classify-risk",
    response_model=ClauseRiskResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def classify_risk_endpoint(request: ClauseRiskRequest):
    """
    Internal endpoint for Stage 2 Legal-BERT single clause risk classification.
    """
    if not request.clause_text.strip():
        raise HTTPException(status_code=400, detail="Clause text must not be empty.")

    result = classify_clause_risk(
        clause_text=request.clause_text,
        rule_findings=request.rule_findings
    )
    return ClauseRiskResponse(**result)


@router.post(
    "/classify-document-risk",
    response_model=DocumentRiskResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def classify_document_risk_endpoint(request: DocumentRiskRequest):
    """
    Internal endpoint for multi-clause document risk classification with per-clause failure isolation (Chapter 16.5)
    and strict output validation / conflict resolution (Chapter 16.9, Decision R-03).
    """
    if request.clauses is None:
        raise HTTPException(status_code=400, detail="Clauses list cannot be null.")

    result = classify_document_clauses_risk(
        clauses=request.clauses,
        rule_findings=request.rule_findings
    )
    return DocumentRiskResponse(**result)


@router.post(
    "/validate-risk-output",
    response_model=OutputValidationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def validate_risk_output_endpoint(request: OutputValidationRequest):
    """
    Internal endpoint for explicit output validation and conflict resolution (Chapter 56.9, Decision R-03).
    """
    result_item = validate_and_resolve_clause_risk(
        clause=request.clause,
        raw_classification=request.raw_classification,
        rule_findings=request.rule_findings
    )
    # Ensure backwards compatible severity field
    result_item["severity"] = result_item["final_severity"] or "Safe"

    return OutputValidationResponse(
        success=True,
        result=result_item
    )
