"""
ClarifAI Legal Clause Categorization Router
Internal endpoint for categorizing clause records into the fixed 8-category PRD set.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.clause_categorization import ClauseCategorizationRequest, ClauseCategorizationResponse
from app.services.clause_categorization_service import categorize_clause_records
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Clause Processing"])


@router.post(
    "/categorize-clauses",
    response_model=ClauseCategorizationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def categorize_clauses_endpoint(payload: ClauseCategorizationRequest):
    """
    Internal endpoint to categorize segmented legal clause records into the fixed 8-category set.
    """
    if payload.clauses is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_INPUT",
                "message": "Clauses list field cannot be null."
            }
        )

    raw_clauses = [c.model_dump() for c in payload.clauses]
    result = categorize_clause_records(raw_clauses)
    return ClauseCategorizationResponse(**result)
