"""
RAG Pipeline & Two-Stage Gating Unit Tests (AI-PHASE-RAG)
Verifies Stage 1 Relevance Gate, Stage 2 Sufficiency Gate, threshold boundary behavior,
ownership-scoped Qdrant retrieval, end-to-end validated evidence set generation,
controlled no-answer decision path, and API router endpoint.
"""

import pytest
from qdrant_client import QdrantClient
from fastapi.testclient import TestClient

from app.main import app
from app.services.qdrant_service import ensure_collection_exists, index_document_clauses
from app.services.rag_service import (
    evaluate_relevance_stage,
    evaluate_sufficiency_stage,
    retrieve_and_evaluate_evidence
)

client = TestClient(app)


@pytest.fixture
def memory_qdrant_client():
    """Provides an isolated in-memory QdrantClient instance for each test."""
    test_client = QdrantClient(":memory:")
    ensure_collection_exists(test_client)
    return test_client


def test_relevance_stage_independently():
    """Unit test: Stage 1 Relevance Gate filters out candidates below threshold."""
    candidates = [
        {"clause_id": "c1", "score": 0.85},
        {"clause_id": "c2", "score": 0.60},
        {"clause_id": "c3", "score": 0.68}
    ]

    passed, rel_candidates = evaluate_relevance_stage(candidates, threshold=0.65)
    assert passed is True
    assert len(rel_candidates) == 2
    assert [c["clause_id"] for c in rel_candidates] == ["c1", "c3"]


def test_relevance_stage_failure():
    candidates = [
        {"clause_id": "c1", "score": 0.50},
        {"clause_id": "c2", "score": 0.60}
    ]

    passed, rel_candidates = evaluate_relevance_stage(candidates, threshold=0.65)
    assert passed is False
    assert len(rel_candidates) == 0


def test_sufficiency_stage_independently():
    """Unit test: Stage 2 Sufficiency Gate requires top score >= sufficiency threshold."""
    relevant_candidates = [
        {"clause_id": "c1", "score": 0.75},
        {"clause_id": "c2", "score": 0.68}
    ]

    suf_passed = evaluate_sufficiency_stage(relevant_candidates, threshold=0.70)
    assert suf_passed is True


def test_sufficiency_stage_failure():
    relevant_candidates = [
        {"clause_id": "c1", "score": 0.68},
        {"clause_id": "c2", "score": 0.66}
    ]

    suf_passed = evaluate_sufficiency_stage(relevant_candidates, threshold=0.70)
    assert suf_passed is False


def test_threshold_boundary_behavior():
    """Threshold-boundary test: verifies exact behavior just above and below configured thresholds."""
    # Score 0.64 is below 0.65 relevance threshold
    rel_passed_below, _ = evaluate_relevance_stage([{"score": 0.64}], threshold=0.65)
    assert rel_passed_below is False

    # Score 0.65 passes relevance threshold
    rel_passed_at, rel_cands = evaluate_relevance_stage([{"score": 0.65}], threshold=0.65)
    assert rel_passed_at is True
    assert len(rel_cands) == 1

    # Score 0.69 passes relevance (0.65) but fails sufficiency (0.70)
    suf_passed_below = evaluate_sufficiency_stage([{"score": 0.69}], threshold=0.70)
    assert suf_passed_below is False

    # Score 0.70 passes sufficiency (0.70)
    suf_passed_at = evaluate_sufficiency_stage([{"score": 0.70}], threshold=0.70)
    assert suf_passed_at is True


def test_end_to_end_rag_retrieval_and_gating_success(memory_qdrant_client):
    """End-to-end test: indexed document clause matches user question, passes both gates, returns validated evidence."""
    user_id = "user_rag_01"
    document_id = "doc_rag_01"
    clauses = [
        {
            "position": 1,
            "clause_id": "c1",
            "text": "Either party may terminate this Agreement upon thirty (30) days prior written notice.",
            "severity": "Safe",
            "categories": ["Termination"]
        }
    ]

    index_document_clauses(user_id=user_id, document_id=document_id, clauses=clauses, client=memory_qdrant_client)

    question = "What is the notice period required to terminate this agreement?"
    res = retrieve_and_evaluate_evidence(
        user_id=user_id,
        document_id=document_id,
        question=question,
        client=memory_qdrant_client
    )

    assert res["has_sufficient_evidence"] is True
    assert res["relevance_gate_passed"] is True
    assert res["sufficiency_gate_passed"] is True
    assert res["no_answer_reason"] is None
    assert len(res["validated_evidence"]) >= 1
    assert res["validated_evidence"][0]["clause_id"] == "c1"


def test_end_to_end_rag_no_answer_unsupported_question(memory_qdrant_client):
    """End-to-end test: question with no supporting evidence in document fails gating, returns controlled no-answer decision."""
    user_id = "user_rag_02"
    document_id = "doc_rag_02"
    clauses = [
        {"position": 1, "clause_id": "c1", "text": "Customer shall pay all invoices within 30 days."}
    ]

    index_document_clauses(user_id=user_id, document_id=document_id, clauses=clauses, client=memory_qdrant_client)

    # Irrelevant question with strict sufficiency threshold (0.85) to trigger controlled no-answer
    question = "What are the rules regarding intellectual property patent licensing in China?"
    res = retrieve_and_evaluate_evidence(
        user_id=user_id,
        document_id=document_id,
        question=question,
        sufficiency_threshold=0.85,
        client=memory_qdrant_client
    )

    assert res["has_sufficient_evidence"] is False
    assert res["no_answer_reason"] is not None
    assert len(res["validated_evidence"]) == 0


def test_ownership_scoping(memory_qdrant_client):
    """Verifies retrieval is strictly scoped to supplied user_id and document_id."""
    user_A = "user_alpha"
    user_B = "user_beta"
    doc_A = "doc_alpha"

    clauses_A = [{"position": 1, "clause_id": "cA", "text": "User Alpha confidential clause."}]
    index_document_clauses(user_id=user_A, document_id=doc_A, clauses=clauses_A, client=memory_qdrant_client)

    question = "Confidential clause"

    # User B queries User A's document under User B's user_id -> 0 matches / controlled no-answer
    res = retrieve_and_evaluate_evidence(
        user_id=user_B,
        document_id=doc_A,
        question=question,
        client=memory_qdrant_client
    )

    assert res["has_sufficient_evidence"] is False
    assert len(res["validated_evidence"]) == 0


def test_rag_api_endpoint():
    """API endpoint test for POST /api/v1/rag/retrieve-evidence."""
    payload = {
        "user_id": "api_user",
        "document_id": "api_doc",
        "question": "Sample API test question?"
    }

    response = client.post("/api/v1/rag/retrieve-evidence", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "has_sufficient_evidence" in data
    assert "relevance_gate_passed" in data
    assert "sufficiency_gate_passed" in data
    assert data["has_sufficient_evidence"] is False
