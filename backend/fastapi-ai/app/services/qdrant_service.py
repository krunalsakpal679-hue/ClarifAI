"""
ClarifAI Qdrant Vector Database Integration & Ownership-Scoped Retrieval Service (AI-PHASE-QDRANT)
Enforces strict dual-field (user_id + document_id) hard filtering on every query path.
Per PRD v2.3 Chapter 28.4, Chapter 28.5, and Chapter 50.
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType
)

from app.core.config import settings
from app.services.embedding_service import generate_clause_embedding, generate_query_embedding, get_embedding_dimension
from app.models.common import SCHEMA_VERSION

logger = logging.getLogger(__name__)

# Single global cached client instance
_qdrant_client_instance: Optional[QdrantClient] = None


def get_qdrant_client(in_memory: bool = False) -> QdrantClient:
    """
    Lazy loads and returns a QdrantClient instance.
    If in_memory=True, QDRANT_URL is ':memory:', or server is unreachable, falls back to in-memory client.
    """
    global _qdrant_client_instance
    if in_memory or settings.QDRANT_URL == ":memory:":
        if _qdrant_client_instance is None or not getattr(_qdrant_client_instance, "_is_memory", False):
            _qdrant_client_instance = QdrantClient(":memory:")
            setattr(_qdrant_client_instance, "_is_memory", True)
        return _qdrant_client_instance

    if _qdrant_client_instance is None:
        try:
            logger.info(f"Connecting to Qdrant server at '{settings.QDRANT_URL}'...")
            if settings.QDRANT_API_KEY:
                client_candidate = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            else:
                client_candidate = QdrantClient(url=settings.QDRANT_URL)
            # Test connectivity
            client_candidate.get_collections()
            _qdrant_client_instance = client_candidate
        except Exception as exc:
            logger.warning(f"Could not connect to Qdrant at '{settings.QDRANT_URL}': {exc}. Falling back to in-memory Qdrant instance.")
            _qdrant_client_instance = QdrantClient(":memory:")
            setattr(_qdrant_client_instance, "_is_memory", True)

    return _qdrant_client_instance


def ensure_collection_exists(client: Optional[QdrantClient] = None) -> bool:
    """
    Ensures that the Qdrant collection exists with 768 dimensions, Cosine distance metric,
    and indexed payload fields for user_id and document_id.
    """
    if client is None:
        client = get_qdrant_client()

    collection_name = settings.QDRANT_COLLECTION_NAME
    dim = 768  # Matches Multilingual-E5 output from AI-PHASE-EMBEDDINGS

    try:
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)

        if not exists:
            logger.info(f"Creating Qdrant collection '{collection_name}' with dim={dim}, distance=COSINE.")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )

            # Create payload index on user_id and document_id if not in-memory client
            if not getattr(client, "_is_memory", False):
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="user_id",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="document_id",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                except Exception as idx_err:
                    logger.debug(f"Payload index creation note: {idx_err}")

        return True
    except Exception as exc:
        logger.error(f"Failed to ensure Qdrant collection '{collection_name}': {exc}")
        raise RuntimeError(f"Qdrant collection setup error: {exc}")


def generate_deterministic_point_id(user_id: str, document_id: str, clause_id: str) -> str:
    """
    Generates a deterministic UUID string for a Qdrant point based on user_id, document_id, and clause_id.
    """
    composite_key = f"{user_id}_{document_id}_{clause_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, composite_key))


def index_document_clauses(
    user_id: str,
    document_id: str,
    clauses: List[Dict[str, Any]],
    client: Optional[QdrantClient] = None
) -> Dict[str, Any]:
    """
    Indexes a document's clauses into Qdrant after classification/simplification.
    Each point payload contains clause_id, document_id, user_id, position, language, and clause metadata.

    Args:
        user_id: Owner user ID string.
        document_id: Document ID string.
        clauses: List of clause dicts with text and metadata.
        client: Optional QdrantClient instance.

    Returns:
        Dict containing indexing outcome status.
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id must be a non-empty string.")
    if not document_id or not document_id.strip():
        raise ValueError("document_id must be a non-empty string.")
    if not clauses:
        raise ValueError("Clauses list cannot be empty for indexing.")

    if client is None:
        client = get_qdrant_client()

    ensure_collection_exists(client)
    collection_name = settings.QDRANT_COLLECTION_NAME

    points = []
    for idx, clause in enumerate(clauses):
        c_id = str(clause.get("clause_id", f"clause_{idx + 1}"))
        c_text = clause.get("original_text") or clause.get("text", "")

        if not c_text.strip():
            logger.warning(f"Skipping point creation for empty clause {c_id} in doc {document_id}.")
            continue

        # Get or generate vector embedding (768 dims)
        vector = clause.get("embedding")
        if not vector or len(vector) != 768:
            vector = generate_clause_embedding(c_text)

        point_uuid = generate_deterministic_point_id(user_id, document_id, c_id)

        payload = {
            "clause_id": c_id,
            "document_id": document_id,
            "user_id": user_id,
            "position": clause.get("position", idx + 1),
            "language": clause.get("language", "en"),
            "text": clause.get("text", c_text),
            "original_text": clause.get("original_text", c_text),
            "severity": clause.get("severity", clause.get("final_severity", "Safe")),
            "categories": clause.get("categories", []),
            "simplified_text": clause.get("simplified_text", ""),
            "why_flagged": clause.get("why_flagged", "")
        }

        points.append(PointStruct(id=point_uuid, vector=vector, payload=payload))

    if not points:
        raise ValueError("No valid points generated for document indexing.")

    client.upsert(collection_name=collection_name, points=points)
    logger.info(f"Successfully indexed {len(points)} clauses into Qdrant for doc '{document_id}', user '{user_id}'.")

    return {
        "success": True,
        "indexed_points": len(points),
        "document_id": document_id,
        "user_id": user_id,
        "collection_name": collection_name,
        "schema_version": SCHEMA_VERSION
    }


def query_clauses_scoped(
    user_id: str,
    document_id: str,
    query_vector: List[float],
    top_k: int = 5,
    client: Optional[QdrantClient] = None
) -> List[Dict[str, Any]]:
    """
    STRICT OWNERSHIP-SCOPED QUERY HELPER.
    This is the ONLY supported function to query Qdrant anywhere in this codebase.
    Guarantees every retrieval is filtered by both user_id and document_id.

    Args:
        user_id: Owner user ID string (MANDATORY).
        document_id: Target document ID string (MANDATORY).
        query_vector: 768-dimensional float list.
        top_k: Maximum matches to retrieve.
        client: Optional QdrantClient instance.

    Returns:
        List of matching clause payload dicts augmented with similarity score.
    """
    # HARD SAFETY AUDIT ENFORCEMENT: Reject any call with missing or empty user_id or document_id
    if not user_id or not user_id.strip():
        raise ValueError("Ownership Violation: user_id is MANDATORY and cannot be empty for Qdrant retrieval.")
    if not document_id or not document_id.strip():
        raise ValueError("Ownership Violation: document_id is MANDATORY and cannot be empty for Qdrant retrieval.")
    if not query_vector or len(query_vector) != 768:
        raise ValueError("Query Vector Error: query_vector must be a non-empty 768-dimensional float list.")

    if client is None:
        client = get_qdrant_client()

    collection_name = settings.QDRANT_COLLECTION_NAME
    ensure_collection_exists(client)

    # HARD QDRANT PAYLOAD FILTER: Must match BOTH user_id and document_id
    hard_filter = Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            FieldCondition(key="document_id", match=MatchValue(value=document_id))
        ]
    )

    try:
        # Use query_points for modern qdrant-client >= 1.7.0
        if hasattr(client, "query_points"):
            search_res = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=hard_filter,
                limit=top_k
            ).points
        else:
            search_res = client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=hard_filter,
                limit=top_k
            )

        results = []
        for hit in search_res:
            res_dict = dict(hit.payload)
            res_dict["score"] = round(float(hit.score), 4)
            results.append(res_dict)

        return results
    except Exception as exc:
        logger.warning(f"Scoped Qdrant query returned 0 matches for user '{user_id}', doc '{document_id}': {exc}")
        return []


def delete_document_points(
    user_id: str,
    document_id: str,
    client: Optional[QdrantClient] = None
) -> Dict[str, Any]:
    """
    Deletes all vector points associated with a specific document_id and user_id.
    Called by the backend deletion cascade (PRD active-data deletion model).
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id must be a non-empty string.")
    if not document_id or not document_id.strip():
        raise ValueError("document_id must be a non-empty string.")

    if client is None:
        client = get_qdrant_client()

    collection_name = settings.QDRANT_COLLECTION_NAME
    ensure_collection_exists(client)

    delete_filter = Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            FieldCondition(key="document_id", match=MatchValue(value=document_id))
        ]
    )

    try:
        client.delete(
            collection_name=collection_name,
            points_selector=delete_filter
        )
        logger.info(f"Deleted points for document '{document_id}', user '{user_id}' from Qdrant.")
        return {
            "success": True,
            "deleted_document_id": document_id,
            "user_id": user_id,
            "schema_version": SCHEMA_VERSION
        }
    except Exception as exc:
        logger.error(f"Failed to delete Qdrant points for doc '{document_id}': {exc}")
        raise RuntimeError(f"Qdrant deletion error: {exc}")


def reindex_document_clauses(
    user_id: str,
    document_id: str,
    clauses: List[Dict[str, Any]],
    client: Optional[QdrantClient] = None
) -> Dict[str, Any]:
    """
    Re-indexes a document's clauses by first purging existing points and then upserting new clause points.
    """
    if client is None:
        client = get_qdrant_client()

    # 1. Delete existing points for document
    delete_document_points(user_id=user_id, document_id=document_id, client=client)

    # 2. Index updated clauses
    return index_document_clauses(user_id=user_id, document_id=document_id, clauses=clauses, client=client)
