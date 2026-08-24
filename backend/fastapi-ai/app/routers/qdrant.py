"""
ClarifAI Qdrant Vector Database Integration Router (AI-PHASE-QDRANT)
Exposes endpoints for document indexing, strict ownership-scoped querying, and deletion cascade.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.qdrant import (
    QdrantIndexRequest,
    QdrantIndexResponse,
    QdrantQueryRequest,
    QdrantQueryResponse,
    QdrantDeleteRequest,
    QdrantDeleteResponse
)
from app.services.qdrant_service import (
    index_document_clauses,
    query_clauses_scoped,
    delete_document_points
)
from app.services.embedding_service import generate_query_embedding
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1/qdrant", tags=["Qdrant Vector DB"])


@router.post(
    "/index-document",
    response_model=QdrantIndexResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def index_document_endpoint(request: QdrantIndexRequest):
    """
    Internal endpoint to index document clauses into Qdrant vector database.
    """
    try:
        res = index_document_clauses(
            user_id=request.user_id,
            document_id=request.document_id,
            clauses=request.clauses
        )
        return QdrantIndexResponse(**res)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Qdrant document indexing failed: {exc}")


@router.post(
    "/query",
    response_model=QdrantQueryResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def query_scoped_endpoint(request: QdrantQueryRequest):
    """
    Internal endpoint for ownership-scoped clause retrieval.
    HARD REQUIRES user_id and document_id for security isolation.
    """
    # 1. Resolve query vector
    if request.query_vector and len(request.query_vector) == 768:
        q_vector = request.query_vector
    elif request.query_text and request.query_text.strip():
        q_vector = generate_query_embedding(request.text if hasattr(request, "text") else request.query_text)
    else:
        raise HTTPException(status_code=400, detail="Either query_text or a valid 768-dim query_vector must be provided.")

    try:
        results = query_clauses_scoped(
            user_id=request.user_id,
            document_id=request.document_id,
            query_vector=q_vector,
            top_k=request.top_k or 5
        )
        return QdrantQueryResponse(
            success=True,
            results=results,
            total_matches=len(results),
            user_id=request.user_id,
            document_id=request.document_id
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scoped Qdrant query execution failed: {exc}")


@router.delete(
    "/delete-document",
    response_model=QdrantDeleteResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def delete_document_endpoint(request: QdrantDeleteRequest):
    """
    Internal endpoint to remove document points from Qdrant during active-data deletion cascade.
    """
    try:
        res = delete_document_points(
            user_id=request.user_id,
            document_id=request.document_id
        )
        return QdrantDeleteResponse(**res)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Qdrant document points deletion failed: {exc}")
