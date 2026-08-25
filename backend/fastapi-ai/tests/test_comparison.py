"""
Pairwise Contract Document Clause Comparison Service Unit Tests (AI-PHASE-COMPARISON)
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.qdrant_service import get_qdrant_client, index_document_clauses, delete_document_points
from app.services.comparison_service import compare_documents, generate_difference_explanation
from app.models.comparison import ComparisonRequest, ComparisonResponse

client = TestClient(app)


@pytest.fixture
def memory_qdrant():
    """Provides an in-memory Qdrant client fixture for test isolation."""
    q_client = get_qdrant_client(in_memory=True)
    yield q_client


def test_near_identical_document_pair_mostly_matched(memory_qdrant):
    """Verifies that a near-identical document pair yields mostly MATCHED results."""
    user_id = "user_comp_01"
    doc_a = "doc_comp_near_a"
    doc_b = "doc_comp_near_b"

    clauses_a = [
        {"clause_id": "c1", "position": 1, "text": "This Agreement shall be governed by the laws of California.", "severity": "Safe"},
        {"clause_id": "c2", "position": 2, "text": "Either party may terminate this agreement upon 30 days written notice.", "severity": "Safe"}
    ]

    # Doc B is identical to Doc A
    clauses_b = [
        {"clause_id": "c1_b", "position": 1, "text": "This Agreement shall be governed by the laws of California.", "severity": "Safe"},
        {"clause_id": "c2_b", "position": 2, "text": "Either party may terminate this agreement upon 30 days written notice.", "severity": "Safe"}
    ]

    index_document_clauses(user_id=user_id, document_id=doc_a, clauses=clauses_a, client=memory_qdrant)
    index_document_clauses(user_id=user_id, document_id=doc_b, clauses=clauses_b, client=memory_qdrant)

    res = compare_documents(
        user_id=user_id,
        document_id_a=doc_a,
        document_id_b=doc_b,
        qdrant_client=memory_qdrant
    )

    assert res["success"] is True
    assert res["matched_count"] == 2
    assert res["changed_count"] == 0
    assert res["missing_count"] == 0
    assert res["is_low_confidence"] is False
    assert len(res["comparison_results"]) == 2
    assert res["comparison_results"][0]["classification"] == "MATCHED"


def test_substantially_changed_document_pair_changed_and_missing(memory_qdrant):
    """Verifies that a modified clause pair yields CHANGED classification with grounded LLM explanation."""
    user_id = "user_comp_02"
    doc_a = "doc_comp_mod_a"
    doc_b = "doc_comp_mod_b"

    clauses_a = [
        {"clause_id": "c1", "position": 1, "text": "Supplier warrants all products for a period of twelve months from delivery.", "severity": "Safe"}
    ]

    clauses_b = [
        {"clause_id": "c1_b", "position": 1, "text": "Supplier disclaims all express and implied warranties to the maximum extent permitted by law.", "severity": "High"}
    ]

    index_document_clauses(user_id=user_id, document_id=doc_a, clauses=clauses_a, client=memory_qdrant)
    index_document_clauses(user_id=user_id, document_id=doc_b, clauses=clauses_b, client=memory_qdrant)

    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Warranty terms were changed from a 12-month product warranty to a complete disclaiming of all warranties.", reasoning=None))],
        usage=MagicMock(prompt_tokens=20, completion_tokens=15, total_tokens=35)
    )

    res = compare_documents(
        user_id=user_id,
        document_id_a=doc_a,
        document_id_b=doc_b,
        matched_threshold=0.92,
        changed_threshold=0.40,
        qdrant_client=memory_qdrant,
        override_llm_client=mock_llm_client
    )

    assert res["success"] is True
    assert len(res["comparison_results"]) >= 1
    first_item = res["comparison_results"][0]
    assert first_item["classification"] == "CHANGED"
    assert "Warranty terms were changed" in first_item["difference_explanation"]


def test_unavailable_embeddings_raises_structured_error(memory_qdrant):
    """Verifies that attempting comparison on missing/unindexed document IDs raises ValueError."""
    user_id = "user_comp_03"
    
    with pytest.raises(ValueError) as exc_info:
        compare_documents(
            user_id=user_id,
            document_id_a="unindexed_doc_a",
            document_id_b="unindexed_doc_b",
            qdrant_client=memory_qdrant
        )

    assert "unavailable" in str(exc_info.value).lower() or "unindexed" in str(exc_info.value).lower()


def test_low_confidence_indicator_on_different_lengths(memory_qdrant):
    """Verifies that documents of significantly different clause counts trigger low confidence flag."""
    user_id = "user_comp_04"
    doc_a = "doc_long"
    doc_b = "doc_short"

    clauses_a = [
        {"clause_id": f"ca_{i}", "position": i, "text": f"Clause A number {i} text for comparison.", "severity": "Safe"}
        for i in range(1, 6)
    ]
    clauses_b = [
        {"clause_id": "cb_1", "position": 1, "text": "Clause B text.", "severity": "Safe"}
    ]

    index_document_clauses(user_id=user_id, document_id=doc_a, clauses=clauses_a, client=memory_qdrant)
    index_document_clauses(user_id=user_id, document_id=doc_b, clauses=clauses_b, client=memory_qdrant)

    res = compare_documents(
        user_id=user_id,
        document_id_a=doc_a,
        document_id_b=doc_b,
        qdrant_client=memory_qdrant
    )

    assert res["success"] is True
    assert res["is_low_confidence"] is True
    assert res["confidence_warning"] is not None
    assert "differ significantly" in res["confidence_warning"]


def test_defensive_ownership_isolation_cross_user(memory_qdrant):
    """Verifies cross-user isolation: user_2 cannot compare user_1's documents."""
    doc_a = "doc_user1_a"
    doc_b = "doc_user1_b"

    clauses = [{"clause_id": "c1", "position": 1, "text": "Confidential text.", "severity": "Safe"}]
    index_document_clauses(user_id="user_1", document_id=doc_a, clauses=clauses, client=memory_qdrant)
    index_document_clauses(user_id="user_1", document_id=doc_b, clauses=clauses, client=memory_qdrant)

    # user_2 attempts to access user_1's docs -> fails with unavailable index error
    with pytest.raises(ValueError) as exc_info:
        compare_documents(user_id="user_2", document_id_a=doc_a, document_id_b=doc_b, qdrant_client=memory_qdrant)

    assert "unavailable" in str(exc_info.value).lower()


def test_comparison_api_endpoint(memory_qdrant):
    """Verifies POST /api/v1/comparison/compare-documents router endpoint."""
    user_id = "user_comp_api"
    doc_a = "doc_api_a"
    doc_b = "doc_api_b"

    clauses = [{"clause_id": "c1", "position": 1, "text": "Standard agreement clause.", "severity": "Safe"}]
    index_document_clauses(user_id=user_id, document_id=doc_a, clauses=clauses, client=memory_qdrant)
    index_document_clauses(user_id=user_id, document_id=doc_b, clauses=clauses, client=memory_qdrant)

    payload = {
        "user_id": user_id,
        "document_id_a": doc_a,
        "document_id_b": doc_b,
        "matched_threshold": 0.88,
        "changed_threshold": 0.65
    }

    response = client.post("/api/v1/comparison/compare-documents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user_id"] == user_id
    assert data["document_id_a"] == doc_a
    assert data["document_id_b"] == doc_b
    assert "comparison_results" in data
