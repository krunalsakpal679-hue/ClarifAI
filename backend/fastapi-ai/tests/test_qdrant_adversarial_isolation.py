"""
Adversarial Multi-Tenant Qdrant Isolation & Vector Validation Test Suite (BOOK4-PHASE-08)
Validates:
1. Qdrant collection configuration (768-dim, COSINE distance, indexed fields).
2. Multi-tenant document indexing for distinct users (User A and User B).
3. Adversarial cross-user query isolation: User B cannot retrieve User A's vectors/clauses under any conditions.
4. RAG Chatbot cross-user isolation: User B cannot retrieve RAG evidence or chat answers for User A's document.
5. Pairwise Comparison isolation: Cross-user document comparisons fail or isolate vectors strictly.
6. Active-data deletion cascade: Deleting User A's document purges 100% of User A's points and leaves User B's points 100% intact.
"""

import pytest
from qdrant_client import QdrantClient
from fastapi.testclient import TestClient

from app.main import app
from app.services.qdrant_service import (
    ensure_collection_exists,
    index_document_clauses,
    query_clauses_scoped,
    retrieve_all_document_clauses,
    delete_document_points,
    reindex_document_clauses,
    generate_deterministic_point_id
)
from app.services.embedding_service import generate_clause_embedding, generate_query_embedding
from app.services.comparison_service import compare_documents
from app.services.rag_service import retrieve_and_evaluate_evidence
from app.core.config import settings

client = TestClient(app)
INTERNAL_HEADERS = {"X-Internal-Service-Secret": settings.INTERNAL_SERVICE_SECRET} if settings.INTERNAL_SERVICE_SECRET else {}


@pytest.fixture
def memory_client():
    """Provides an isolated in-memory Qdrant instance for test execution."""
    q_client = QdrantClient(":memory:")
    setattr(q_client, "_is_memory", True)
    ensure_collection_exists(q_client)
    return q_client


def test_qdrant_collection_configuration_and_dimension(memory_client):
    """
    Step 1: Confirm collection exists with 768-dim vector configuration and COSINE distance.
    """
    collections = memory_client.get_collections().collections
    assert any(c.name == settings.QDRANT_COLLECTION_NAME for c in collections)

    info = memory_client.get_collection(settings.QDRANT_COLLECTION_NAME)
    assert info.config.params.vectors.size == 768
    assert info.config.params.vectors.distance.name.upper() == "COSINE"


def test_adversarial_two_user_multi_document_indexing_and_isolation(memory_client):
    """
    Steps 2 & 3: Index two distinct documents for two different users and test adversarial cross-retrieval.
    """
    user_a = "user_alpha_uuid_001"
    user_b = "user_beta_uuid_002"
    doc_a = "doc_alpha_contracts_101"
    doc_b = "doc_beta_financials_202"

    clauses_a = [
        {
            "position": 1,
            "clause_id": "clause_a1",
            "text": "The Consultant agrees to maintain strict confidentiality of all proprietary source code.",
            "original_text": "The Consultant agrees to maintain strict confidentiality of all proprietary source code.",
            "language": "en",
            "severity": "High",
            "categories": ["Confidentiality", "IP"],
            "simplified_text": "You must keep all code secret.",
            "why_flagged": "Strict proprietary disclosure terms."
        },
        {
            "position": 2,
            "clause_id": "clause_a2",
            "text": "Either party may terminate this agreement with 60 days written notice.",
            "original_text": "Either party may terminate this agreement with 60 days written notice.",
            "language": "en",
            "severity": "Moderate",
            "categories": ["Termination"],
            "simplified_text": "60 days notice required to cancel.",
            "why_flagged": "Standard termination clause."
        }
    ]

    clauses_b = [
        {
            "position": 1,
            "clause_id": "clause_b1",
            "text": "The Borrower will repay the principal amount within 36 calendar months at 5.5% annual interest.",
            "original_text": "The Borrower will repay the principal amount within 36 calendar months at 5.5% annual interest.",
            "language": "en",
            "severity": "High",
            "categories": ["Payment", "Financial"],
            "simplified_text": "Pay back loan in 3 years with 5.5% interest.",
            "why_flagged": "Fixed term repayment schedule."
        },
        {
            "position": 2,
            "clause_id": "clause_b2",
            "text": "Failure to make payment within 10 days of the due date constitutes default.",
            "original_text": "Failure to make payment within 10 days of the due date constitutes default.",
            "language": "en",
            "severity": "Critical",
            "categories": ["Default", "Payment"],
            "simplified_text": "Default occurs 10 days after missing a payment.",
            "why_flagged": "Short grace period before default."
        }
    ]

    # Index both documents into Qdrant
    res_a = index_document_clauses(user_id=user_a, document_id=doc_a, clauses=clauses_a, client=memory_client)
    res_b = index_document_clauses(user_id=user_b, document_id=doc_b, clauses=clauses_b, client=memory_client)

    assert res_a["success"] is True and res_a["indexed_points"] == 2
    assert res_b["success"] is True and res_b["indexed_points"] == 2

    # Query embeddings
    confidentiality_query = generate_query_embedding("confidentiality and proprietary source code")
    loan_query = generate_query_embedding("loan repayment schedule and interest rate")

    # 1. Legitimate queries succeed
    res_legit_a = query_clauses_scoped(user_id=user_a, document_id=doc_a, query_vector=confidentiality_query, client=memory_client)
    assert len(res_legit_a) >= 1
    assert res_legit_a[0]["user_id"] == user_a
    assert res_legit_a[0]["document_id"] == doc_a
    assert res_legit_a[0]["clause_id"] == "clause_a1"

    res_legit_b = query_clauses_scoped(user_id=user_b, document_id=doc_b, query_vector=loan_query, client=memory_client)
    assert len(res_legit_b) >= 1
    assert res_legit_b[0]["user_id"] == user_b
    assert res_legit_b[0]["document_id"] == doc_b
    assert res_legit_b[0]["clause_id"] == "clause_b1"

    # 2. ADVERSARIAL ATTEMPT 1: User B tries to retrieve User A's document (doc_a) using User B's user_id
    res_adv_1 = query_clauses_scoped(user_id=user_b, document_id=doc_a, query_vector=confidentiality_query, client=memory_client)
    assert len(res_adv_1) == 0, "Security Violation: User B retrieved clauses from User A's document!"

    # 3. ADVERSARIAL ATTEMPT 2: User A tries to retrieve User B's document (doc_b) using User A's user_id
    res_adv_2 = query_clauses_scoped(user_id=user_a, document_id=doc_b, query_vector=loan_query, client=memory_client)
    assert len(res_adv_2) == 0, "Security Violation: User A retrieved clauses from User B's document!"

    # 4. ADVERSARIAL ATTEMPT 3: Retrieve all document clauses scroll isolation
    scroll_adv = retrieve_all_document_clauses(user_id=user_b, document_id=doc_a, client=memory_client)
    assert len(scroll_adv) == 0, "Security Violation: User B retrieved full document scroll from User A's document!"


def test_adversarial_rag_evidence_retrieval_isolation(memory_client):
    """
    Verifies RAG evidence retrieval service strictly isolates between tenants.
    """
    user_a = "user_alpha_rag_1"
    user_b = "user_beta_rag_2"
    doc_a = "doc_rag_secret_a"

    clauses_a = [
        {
            "position": 1,
            "clause_id": "clause_secret",
            "text": "The secret key code is CLARIFAI-TOP-SECRET-KEY.",
            "severity": "High",
            "categories": ["Security"]
        }
    ]

    index_document_clauses(user_id=user_a, document_id=doc_a, clauses=clauses_a, client=memory_client)

    # Legitimate retrieval for User A
    rag_a = retrieve_and_evaluate_evidence(
        user_id=user_a,
        document_id=doc_a,
        question="What is the secret key code?",
        client=memory_client
    )
    assert len(rag_a["validated_evidence"]) >= 1
    assert "CLARIFAI-TOP-SECRET-KEY" in rag_a["validated_evidence"][0]["text"]

    # Adversarial retrieval for User B against doc_a
    rag_b = retrieve_and_evaluate_evidence(
        user_id=user_b,
        document_id=doc_a,
        question="What is the secret key code?",
        client=memory_client
    )
    assert len(rag_b["validated_evidence"]) == 0
    assert rag_b["has_sufficient_evidence"] is False


def test_adversarial_pairwise_comparison_isolation(memory_client):
    """
    Step 5: Confirm pairwise comparison retrieval is ownership-scoped for both documents.
    If User A attempts to compare Doc A with Doc B (owned by User B), comparison fails with missing index error.
    """
    user_a = "user_comp_a"
    user_b = "user_comp_b"
    doc_a = "doc_comp_a"
    doc_b = "doc_comp_b"

    clauses_a = [{"position": 1, "clause_id": "c1", "text": "Terms for Document A."}]
    clauses_b = [{"position": 1, "clause_id": "c1", "text": "Terms for Document B."}]

    index_document_clauses(user_id=user_a, document_id=doc_a, clauses=clauses_a, client=memory_client)
    index_document_clauses(user_id=user_b, document_id=doc_b, clauses=clauses_b, client=memory_client)

    # User A tries to compare doc_a and doc_b under User A's credentials
    # Since doc_b belongs to User B, doc_b has 0 clauses under user_a -> must raise ValueError
    with pytest.raises(ValueError, match="Indexed clauses/embeddings unavailable for Document B"):
        compare_documents(
            user_id=user_a,
            document_id_a=doc_a,
            document_id_b=doc_b,
            qdrant_client=memory_client
        )


def test_post_deletion_point_purge_and_sibling_integrity(memory_client):
    """
    Step 4: Delete User A's document; confirm all its points are gone and User B's points remain intact.
    """
    user_a = "user_del_a"
    user_b = "user_del_b"
    doc_a1 = "doc_del_a1"
    doc_a2 = "doc_del_a2"  # Sibling document of User A
    doc_b1 = "doc_del_b1"  # Document of User B

    index_document_clauses(user_id=user_a, document_id=doc_a1, clauses=[{"position": 1, "clause_id": "ca1", "text": "Doc A1 text."}], client=memory_client)
    index_document_clauses(user_id=user_a, document_id=doc_a2, clauses=[{"position": 1, "clause_id": "ca2", "text": "Doc A2 sibling text."}], client=memory_client)
    index_document_clauses(user_id=user_b, document_id=doc_b1, clauses=[{"position": 1, "clause_id": "cb1", "text": "Doc B1 text."}], client=memory_client)

    # Verify all 3 exist before deletion
    q_vec = generate_query_embedding("text")
    assert len(query_clauses_scoped(user_id=user_a, document_id=doc_a1, query_vector=q_vec, client=memory_client)) == 1
    assert len(query_clauses_scoped(user_id=user_a, document_id=doc_a2, query_vector=q_vec, client=memory_client)) == 1
    assert len(query_clauses_scoped(user_id=user_b, document_id=doc_b1, query_vector=q_vec, client=memory_client)) == 1

    # Delete doc_a1
    del_res = delete_document_points(user_id=user_a, document_id=doc_a1, client=memory_client)
    assert del_res["success"] is True

    # 1. doc_a1 points MUST be 0
    assert len(query_clauses_scoped(user_id=user_a, document_id=doc_a1, query_vector=q_vec, client=memory_client)) == 0
    assert len(retrieve_all_document_clauses(user_id=user_a, document_id=doc_a1, client=memory_client)) == 0

    # 2. doc_a2 (sibling of User A) MUST remain intact
    res_a2 = query_clauses_scoped(user_id=user_a, document_id=doc_a2, query_vector=q_vec, client=memory_client)
    assert len(res_a2) == 1
    assert res_a2[0]["clause_id"] == "ca2"

    # 3. doc_b1 (User B) MUST remain intact
    res_b1 = query_clauses_scoped(user_id=user_b, document_id=doc_b1, query_vector=q_vec, client=memory_client)
    assert len(res_b1) == 1
    assert res_b1[0]["clause_id"] == "cb1"


def test_api_router_adversarial_isolation():
    """
    Tests isolation via FastAPI HTTP Router endpoints with authentication.
    """
    user_a = "http_user_a"
    user_b = "http_user_b"
    doc_a = "http_doc_a"

    # 1. Index document for User A via HTTP API
    index_payload = {
        "user_id": user_a,
        "document_id": doc_a,
        "clauses": [
            {"position": 1, "clause_id": "hc1", "text": "HTTP contract clause for User A."}
        ]
    }
    r_index = client.post("/api/v1/qdrant/index-document", json=index_payload, headers=INTERNAL_HEADERS)
    assert r_index.status_code == 200
    assert r_index.json()["success"] is True

    # 2. Legitimate query for User A
    query_payload_legit = {
        "user_id": user_a,
        "document_id": doc_a,
        "query_text": "contract clause"
    }
    r_query_legit = client.post("/api/v1/qdrant/query", json=query_payload_legit, headers=INTERNAL_HEADERS)
    assert r_query_legit.status_code == 200
    assert r_query_legit.json()["total_matches"] >= 1

    # 3. Adversarial query: User B querying User A's document
    query_payload_adv = {
        "user_id": user_b,
        "document_id": doc_a,
        "query_text": "contract clause"
    }
    r_query_adv = client.post("/api/v1/qdrant/query", json=query_payload_adv, headers=INTERNAL_HEADERS)
    assert r_query_adv.status_code == 200
    assert r_query_adv.json()["total_matches"] == 0, "Security Violation: User B queried User A's document via API!"

    # 4. Delete document via API
    del_payload = {"user_id": user_a, "document_id": doc_a}
    r_del = client.request("DELETE", "/api/v1/qdrant/delete-document", json=del_payload, headers=INTERNAL_HEADERS)
    assert r_del.status_code == 200
    assert r_del.json()["success"] is True

    # 5. Query after deletion returns 0
    r_query_after = client.post("/api/v1/qdrant/query", json=query_payload_legit, headers=INTERNAL_HEADERS)
    assert r_query_after.status_code == 200
    assert r_query_after.json()["total_matches"] == 0
