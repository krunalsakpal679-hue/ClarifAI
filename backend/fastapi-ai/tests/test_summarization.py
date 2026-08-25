"""
BART-Base Summarization Service Unit Tests (AI-PHASE-SUMMARY)
Verifies single section summarization, chunking, 4-field document-level executive summary,
high-risk content prioritization, document-level failure isolation (Chapter 16.4), and API route.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.summarization_service import (
    get_summarization_model_name,
    get_summarization_status,
    summarize_text,
    generate_document_summary,
    BART_MAX_CONTEXT_TOKENS
)

client = TestClient(app)


def test_summarization_model_name():
    name = get_summarization_model_name()
    assert "bart" in name.lower()


def test_summarization_status():
    status = get_summarization_status()
    assert status["loaded"] is True
    assert status["max_context_tokens"] == 1024
    assert status["is_interim_placeholder"] is True


def test_summarize_short_text():
    sample_text = (
        "This Agreement shall commence on January 1, 2026 and continue for a term of one year. "
        "Either party may terminate this agreement upon 30 days written notice to the other party."
    )
    res = summarize_text(sample_text, max_length=50, min_length=10)

    assert isinstance(res["summary"], str)
    assert len(res["summary"].strip()) > 0
    assert res["token_count"] <= 50
    assert res["is_chunked"] is False


def test_summarize_chunked_long_text():
    # Long text exceeding 1024 tokens to trigger chunking strategy
    long_text = "This contract section details party responsibilities and liabilities. " * 150

    res = summarize_text(long_text, max_length=100, min_length=20)

    assert isinstance(res["summary"], str)
    assert len(res["summary"].strip()) > 0
    assert res["token_count"] <= 100
    assert res["is_chunked"] is True
    assert res["num_chunks_processed"] >= 2


def test_generate_document_summary_populates_all_four_fields():
    """Verifies all 4 summary fields (purpose, obligations, key terms, key risks) are populated."""
    clauses = [
        {"position": 1, "clause_id": "1", "text": "This Services Agreement is entered into between Vendor Corp and Customer LLC.", "severity": "Safe"},
        {"position": 2, "clause_id": "2", "text": "Customer shall pay all invoices within 30 days of receipt.", "categories": ["Payment"], "severity": "Safe"},
        {"position": 3, "clause_id": "3", "text": "Vendor disclaims all warranties and accepts no liability whatsoever.", "severity": "High", "categories": ["Liability"]}
    ]
    rule_findings = [
        {"rule_id": "R005", "risk_signal": "Excessive Liability Transfer", "clause_id": "3"}
    ]

    res = generate_document_summary(clauses=clauses, rule_findings=rule_findings)

    assert res["success"] is True
    assert res["summary_status"] == "AVAILABLE"
    assert res["purpose_text"] is not None
    assert res["obligations_text"] is not None
    assert res["key_terms_text"] is not None
    assert res["key_risks_text"] is not None
    assert len(res["key_risks_text"].strip()) > 0


def test_key_risks_no_flagged_clauses_fallback():
    """Verifies fallback when no clauses are flagged as risky."""
    clauses = [
        {"position": 1, "clause_id": "1", "text": "Standard agreement preamble text.", "severity": "Safe"}
    ]

    res = generate_document_summary(clauses=clauses)
    assert res["success"] is True
    assert res["key_risks_text"] == "No high-severity legal risks were identified in this document."


def test_document_level_failure_isolation():
    """
    Chapter 16.4: Summary failure must be surfaced as UNAVAILABLE
    without corrupting or reverting already-complete clause data.
    """
    clauses = [
        {"position": 1, "clause_id": "1", "text": "Sample clause text.", "severity": "Safe"}
    ]

    with patch("app.services.summarization_service.summarize_text", side_effect=RuntimeError("BART generation OOM")):
        res = generate_document_summary(clauses=clauses)

    assert res["success"] is False
    assert res["summary_status"] == "UNAVAILABLE"
    assert "BART generation OOM" in res["summary_error"]
    assert res["purpose_text"] is None
    assert res["key_risks_text"] is None


def test_summarize_document_api_endpoint():
    """API Endpoint test for POST /api/v1/summarize-document."""
    payload = {
        "clauses": [
            {"position": 1, "clause_id": "1", "text": "Agreement between Party A and Party B.", "severity": "Safe"}
        ]
    }

    response = client.post("/api/v1/summarize-document", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["summary_status"] == "AVAILABLE"
    assert data["purpose_text"] is not None
