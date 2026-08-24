"""
ClarifAI RAG Pipeline Router (AI-PHASE-RAG)
Exposes internal endpoint for ownership-scoped RAG evidence retrieval and two-stage gating evaluation.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.rag import RAGRequest, RAGEvaluationResponse
from app.services.rag_service import retrieve_and_evaluate_evidence
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1/rag", tags=["RAG Pipeline"])


@router.post(
    "/retrieve-evidence",
    response_model=RAGEvaluationResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def retrieve_evidence_endpoint(request: RAGRequest):
    """
    Internal endpoint for question embedding, ownership-scoped Qdrant retrieval, and two-stage gating.
    Returns validated evidence set or controlled no-answer decision.
    """
    try:
        res = retrieve_and_evaluate_evidence(
            user_id=request.user_id,
            document_id=request.document_id,
            question=request.question,
            top_k=request.top_k or 5,
            relevance_threshold=request.relevance_threshold,
            sufficiency_threshold=request.sufficiency_threshold
        )
        return RAGEvaluationResponse(**res)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG evidence retrieval & gating failed: {exc}")
