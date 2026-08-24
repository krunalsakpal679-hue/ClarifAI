"""
Multilingual-E5 Embedding Service Unit Tests (AI-PHASE-EMBEDDINGS)
Verifies English/Hindi text embeddings, reproducibility, 768 vector dimension,
failure isolation (Chapter 16.5), and API router endpoints.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding_service import (
    get_embedding_model_name,
    get_embedding_dimension,
    generate_clause_embedding,
    generate_query_embedding,
    generate_document_clause_embeddings,
    get_embedding_status
)

client = TestClient(app)


def test_embedding_model_name():
    name = get_embedding_model_name()
    assert "multilingual-e5" in name.lower()


def test_embedding_dimension():
    dim = get_embedding_dimension()
    assert dim == 768


def test_english_and_hindi_clause_embeddings():
    en_clause = "This Agreement shall be governed by the laws of the State of California."
    hi_clause = "यह समझौता कैलिफोर्निया राज्य के कानूनों द्वारा शासित होगा।"

    en_vector = generate_clause_embedding(en_clause)
    hi_vector = generate_clause_embedding(hi_clause)

    # Verify fixed-length non-empty vectors
    assert len(en_vector) == 768
    assert len(hi_vector) == 768

    # Verify elements are valid floats
    assert isinstance(en_vector[0], float)
    assert isinstance(hi_vector[0], float)


def test_reproducibility_identical_input_produces_identical_vector():
    """Reproducibility test: the same input text produces the exact same vector across repeated runs."""
    clause_text = "Either party may terminate this agreement upon 30 days written notice."

    v1 = generate_clause_embedding(clause_text)
    v2 = generate_clause_embedding(clause_text)

    assert len(v1) == 768
    assert len(v2) == 768
    assert v1 == v2


def test_generate_document_clause_embeddings():
    clauses = [
        {"position": 1, "clause_id": "c1", "original_text": "First clause text for testing.", "severity": "Safe"},
        {"position": 2, "clause_id": "c2", "text": "Second clause text for testing.", "severity": "Low"}
    ]

    res = generate_document_clause_embeddings(clauses)
    assert len(res) == 2
    assert res[0]["embedding_status"] == "SUCCESS"
    assert len(res[0]["embedding"]) == 768
    assert res[0]["embedding_dimension"] == 768
    assert res[1]["embedding_status"] == "SUCCESS"
    assert len(res[1]["embedding"]) == 768


def test_simulated_embedding_failure_handling():
    """Shared failure-handling test: model exception is handled per-clause via failure isolation."""
    clauses = [
        {"position": 1, "clause_id": "c1", "text": "Valid clause text."}
    ]

    with patch("app.services.embedding_service.generate_clause_embedding", side_effect=RuntimeError("Model OOM Exception")):
        res = generate_document_clause_embeddings(clauses)

    assert len(res) == 1
    assert res[0]["embedding_status"] == "FAILED"
    assert res[0]["embedding"] is None
    assert "Model OOM Exception" in res[0]["embedding_error"]


def test_embedding_api_endpoints():
    # Test single query embedding
    single_res = client.post("/api/v1/generate-embedding", json={"text": "What is the penalty?", "is_query": True})
    assert single_res.status_code == 200
    single_data = single_res.json()
    assert len(single_data["embedding"]) == 768
    assert single_data["dimension"] == 768

    # Test batch document clause embeddings
    batch_payload = {
        "clauses": [
            {"position": 1, "clause_id": "c1", "text": "Contract clause text."}
        ]
    }
    batch_res = client.post("/api/v1/generate-embeddings", json=batch_payload)
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["success"] is True
    assert batch_data["vector_dimension"] == 768
    assert len(batch_data["embedded_clauses"]) == 1
    assert batch_data["embedded_clauses"][0]["embedding_status"] == "SUCCESS"
