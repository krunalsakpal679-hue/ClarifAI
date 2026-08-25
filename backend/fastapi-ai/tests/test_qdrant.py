"""
Qdrant Vector Database Integration & Scoped Retrieval Unit Tests (AI-PHASE-QDRANT)
Verifies Qdrant collection creation (768-dim, COSINE), payload schema,
strict ownership-scoped querying (user_id + document_id hard filtering),
cross-user retrieval isolation, deletion cascade, reindexing, and API router endpoints.
Uses in-memory Qdrant instance (:memory:) for fast, isolated execution.
"""

import pytest
from qdrant_client import QdrantClient
from fastapi.testclient import TestClient

from app.main import app
from app.services.qdrant_service import (
    get_qdrant_client,
    ensure_collection_exists,
    index_document_clauses,
    query_clauses_scoped,
    delete_document_points,
    reindex_document_clauses
)
from app.services.embedding_service import generate_clause_embedding, generate_query_embedding

client = TestClient(app)


@pytest.fixture
def memory_qdrant_client():
    """Provides an isolated in-memory QdrantClient instance for each test."""
    test_client = QdrantClient(":memory:")
    ensure_collection_exists(test_client)
    return test_client


def test_collection_creation_schema(memory_qdrant_client):
    """Verifies collection exists with 768 vector dimension and COSINE distance."""
    collections = memory_qdrant_client.get_collections().collections
    assert len(collections) >= 1
    collection_name = collections[0].name

    info = memory_qdrant_client.get_collection(collection_name)
    assert info.config.params.vectors.size == 768
    assert info.config.params.vectors.distance.name.upper() == "COSINE"


def test_index_document_clauses_payload(memory_qdrant_client):
    """Unit test: indexing writes correct payload fields."""
    user_id = "user_test_01"
    document_id = "doc_test_01"
    clauses = [
        {
            "position": 1,
            "clause_id": "c1",
            "text": "This agreement terminates in 30 days.",
            "original_text": "This agreement terminates in 30 days.",
            "language": "en",
            "severity": "Moderate",
            "categories": ["Termination"],
            "simplified_text": "Either party can end this contract with 30 days notice.",
            "why_flagged": "Short termination period."
        }
    ]

    res = index_document_clauses(user_id=user_id, document_id=document_id, clauses=clauses, client=memory_qdrant_client)
    assert res["success"] is True
    assert res["indexed_points"] == 1

    # Verify retrieval contains full payload
    q_vec = generate_query_embedding("termination notice")
    matches = query_clauses_scoped(user_id=user_id, document_id=document_id, query_vector=q_vec, client=memory_qdrant_client)

    assert len(matches) == 1
    hit = matches[0]
    assert hit["clause_id"] == "c1"
    assert hit["user_id"] == user_id
    assert hit["document_id"] == document_id
    assert hit["position"] == 1
    assert hit["language"] == "en"
    assert hit["severity"] == "Moderate"
    assert "Termination" in hit["categories"]


def test_adversarial_mismatched_missing_user_or_doc_id(memory_qdrant_client):
    """Adversarial test: attempt query with missing/empty user_id or document_id and confirm helper raises ValueError."""
    q_vec = generate_query_embedding("sample question")

    # Missing user_id
    with pytest.raises(ValueError, match="user_id is MANDATORY"):
        query_clauses_scoped(user_id="", document_id="doc_123", query_vector=q_vec, client=memory_qdrant_client)

    # Missing document_id
    with pytest.raises(ValueError, match="document_id is MANDATORY"):
        query_clauses_scoped(user_id="user_123", document_id="", query_vector=q_vec, client=memory_qdrant_client)

    # Missing query_vector
    with pytest.raises(ValueError, match="query_vector must be a non-empty"):
        query_clauses_scoped(user_id="user_123", document_id="doc_123", query_vector=[], client=memory_qdrant_client)


def test_adversarial_two_user_cross_user_isolation(memory_qdrant_client):
    """
    Adversarial multi-tenant isolation test:
    User A's query for User A's document NEVER returns User B's clauses.
    """
    user_A = "user_alpha_101"
    user_B = "user_beta_202"
    doc_A = "doc_alpha_1001"
    doc_B = "doc_beta_2002"

    clauses_A = [{"position": 1, "clause_id": "cA1", "text": "Confidentiality obligation for User Alpha."}]
    clauses_B = [{"position": 1, "clause_id": "cB1", "text": "Confidentiality obligation for User Beta."}]

    index_document_clauses(user_id=user_A, document_id=doc_A, clauses=clauses_A, client=memory_qdrant_client)
    index_document_clauses(user_id=user_B, document_id=doc_B, clauses=clauses_B, client=memory_qdrant_client)

    q_vec = generate_query_embedding("Confidentiality obligation")

    # User A queries User A's document
    res_A = query_clauses_scoped(user_id=user_A, document_id=doc_A, query_vector=q_vec, client=memory_qdrant_client)
    assert len(res_A) == 1
    assert res_A[0]["user_id"] == user_A
    assert res_A[0]["document_id"] == doc_A
    assert res_A[0]["clause_id"] == "cA1"

    # User A attempts to query User B's document_id under User A's credentials -> 0 matches
    res_cross = query_clauses_scoped(user_id=user_A, document_id=doc_B, query_vector=q_vec, client=memory_qdrant_client)
    assert len(res_cross) == 0

    # User B queries User B's document
    res_B = query_clauses_scoped(user_id=user_B, document_id=doc_B, query_vector=q_vec, client=memory_qdrant_client)
    assert len(res_B) == 1
    assert res_B[0]["user_id"] == user_B
    assert res_B[0]["clause_id"] == "cB1"


def test_deletion_cascade(memory_qdrant_client):
    """Deletion test: confirm deletion removes all of a document's points and none of a sibling document's."""
    user_id = "user_del_test"
    doc_1 = "doc_to_delete"
    doc_2 = "doc_to_keep"

    clauses_1 = [{"position": 1, "clause_id": "c1", "text": "Doc 1 clause text."}]
    clauses_2 = [{"position": 1, "clause_id": "c2", "text": "Doc 2 clause text."}]

    index_document_clauses(user_id=user_id, document_id=doc_1, clauses=clauses_1, client=memory_qdrant_client)
    index_document_clauses(user_id=user_id, document_id=doc_2, clauses=clauses_2, client=memory_qdrant_client)

    # Perform active-data deletion cascade for doc_1
    del_res = delete_document_points(user_id=user_id, document_id=doc_1, client=memory_qdrant_client)
    assert del_res["success"] is True

    q_vec = generate_query_embedding("clause text")

    # doc_1 points must return 0 hits
    hits_doc1 = query_clauses_scoped(user_id=user_id, document_id=doc_1, query_vector=q_vec, client=memory_qdrant_client)
    assert len(hits_doc1) == 0

    # doc_2 points must remain 100% intact
    hits_doc2 = query_clauses_scoped(user_id=user_id, document_id=doc_2, query_vector=q_vec, client=memory_qdrant_client)
    assert len(hits_doc2) == 1
    assert hits_doc2[0]["clause_id"] == "c2"


def test_reindex_document_clauses(memory_qdrant_client):
    """Reindex test: verify reindexing purges old points and inserts updated clause vectors."""
    user_id = "user_reindex"
    doc_id = "doc_reindex"

    initial_clauses = [{"position": 1, "clause_id": "c1", "text": "Original text before reindexing."}]
    index_document_clauses(user_id=user_id, document_id=doc_id, clauses=initial_clauses, client=memory_qdrant_client)

    updated_clauses = [{"position": 1, "clause_id": "c1", "text": "Updated text after reindexing."}]
    reindex_res = reindex_document_clauses(user_id=user_id, document_id=doc_id, clauses=updated_clauses, client=memory_qdrant_client)

    assert reindex_res["success"] is True
    assert reindex_res["indexed_points"] == 1

    q_vec = generate_query_embedding("Updated text")
    matches = query_clauses_scoped(user_id=user_id, document_id=doc_id, query_vector=q_vec, client=memory_qdrant_client)
    assert len(matches) == 1
    assert matches[0]["text"] == "Updated text after reindexing."


def test_qdrant_api_endpoints():
    """API endpoints test for /api/v1/qdrant/index-document, /query, and /delete-document."""
    user_id = "api_user_1"
    doc_id = "api_doc_1"

    index_payload = {
        "user_id": user_id,
        "document_id": doc_id,
        "clauses": [
            {"position": 1, "clause_id": "api_c1", "text": "API testing clause text."}
        ]
    }

    # 1. Index document API call
    index_res = client.post("/api/v1/qdrant/index-document", json=index_payload)
    assert index_res.status_code == 200
    assert index_res.json()["success"] is True

    # 2. Query scoped API call
    query_payload = {
        "user_id": user_id,
        "document_id": doc_id,
        "query_text": "API testing query text",
        "top_k": 5
    }
    query_res = client.post("/api/v1/qdrant/query", json=query_payload)
    assert query_res.status_code == 200
    q_data = query_res.json()
    assert q_data["success"] is True
    assert q_data["user_id"] == user_id
    assert q_data["document_id"] == doc_id

    # 3. Delete document API call
    delete_payload = {
        "user_id": user_id,
        "document_id": doc_id
    }
    delete_res = client.request("DELETE", "/api/v1/qdrant/delete-document", json=delete_payload)
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True
