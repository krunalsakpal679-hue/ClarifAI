"""
ClarifAI Multilingual Embedding Router (AI-PHASE-EMBEDDINGS)
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.embedding import (
    EmbeddingRequest,
    EmbeddingResponse,
    SingleEmbeddingRequest,
    SingleEmbeddingResponse
)
from app.services.embedding_service import (
    generate_clause_embedding,
    generate_query_embedding,
    generate_document_clause_embeddings,
    get_embedding_model_name,
    get_embedding_dimension
)
from app.core.security import verify_internal_secret

router = APIRouter(prefix="/api/v1", tags=["Embeddings"])


@router.post(
    "/generate-embedding",
    response_model=SingleEmbeddingResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def generate_single_embedding_endpoint(request: SingleEmbeddingRequest):
    """
    Internal endpoint for single passage or query 768-dim vector embedding generation using Multilingual-E5.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text for embedding must not be empty.")

    if request.is_query:
        vector = generate_query_embedding(request.text)
    else:
        vector = generate_clause_embedding(request.text)

    return SingleEmbeddingResponse(
        embedding=vector,
        dimension=len(vector),
        model_name=get_embedding_model_name()
    )


@router.post(
    "/generate-embeddings",
    response_model=EmbeddingResponse,
    dependencies=[Depends(verify_internal_secret)]
)
async def generate_embeddings_endpoint(request: EmbeddingRequest):
    """
    Internal endpoint for batch document clause 768-dim vector embedding generation using Multilingual-E5.
    """
    if request.clauses is None:
        raise HTTPException(status_code=400, detail="Clauses list cannot be null.")

    embedded_clauses = generate_document_clause_embeddings(request.clauses)
    dim = get_embedding_dimension()

    return EmbeddingResponse(
        success=True,
        model_name=get_embedding_model_name(),
        vector_dimension=dim,
        total_clauses=len(embedded_clauses),
        embedded_clauses=embedded_clauses
    )
