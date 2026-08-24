"""
Legal-BERT Risk Classification Service Unit Tests (AI-PHASE-LEGAL-BERT-01)
Verifies 4-level severity mapping, contextual rule findings integration,
per-clause failure isolation (Chapter 16.5), and omission of numeric risk scores.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.risk_service import (
    get_legal_bert_model_name,
    get_legal_bert_status,
    classify_clause_risk,
    classify_document_clauses_risk,
    APPROVED_SEVERITY_LABELS
)

client = TestClient(app)


def test_legal_bert_model_name():
    name = get_legal_bert_model_name()
    assert "legal-bert" in name.lower()


def test_legal_bert_status():
    status = get_legal_bert_status()
    assert status["loaded"] is True
    assert status["num_labels"] == 4
    assert set(status["approved_severities"]) == {"High", "Moderate", "Low", "Safe"}
    assert status["is_interim_placeholder"] is True


def test_classify_clause_risk_four_severities_validity():
    test_clauses = [
        "This Agreement shall automatically renew for additional 1-year terms unless notice is given 30 days prior.",
        "Either party may terminate this agreement at any time for convenience upon 60 days written notice.",
        "The Vendor disclaims all warranties, express or implied, including fitness for a particular purpose.",
        "This agreement is governed by the laws of California."
    ]

    for clause in test_clauses:
        res = classify_clause_risk(clause)
        # Verify severity is strictly one of the 4 approved values
        assert res["severity"] in {"High", "Moderate", "Low", "Safe"}
        assert res["logits_shape"] == [1, 4]
        assert 0.0 <= res["confidence"] <= 1.0


def test_classify_clause_risk_with_contextual_rule_findings():
    clause = "This Agreement automatically renews each year unless terminated."
    rule_findings = [{"rule_id": "R001", "risk_signal": "Auto-Renewal", "clause_id": "1"}]

    res = classify_clause_risk(clause, rule_findings=rule_findings)
    assert res["severity"] in {"High", "Moderate", "Low", "Safe"}
    assert res["rule_findings_included"] is True


def test_per_clause_failure_isolation():
    """Chapter 16.5: A single clause classification failure must never abort sibling clauses."""
    clauses = [
        {"position": 1, "clause_id": "1", "text": "Valid clause 1 about payment terms."},
        {"position": 2, "clause_id": "2", "text": "   "},  # Empty invalid clause that triggers fallback
        {"position": 3, "clause_id": "3", "text": "Valid clause 3 about confidentiality."}
    ]

    res = classify_document_clauses_risk(clauses)
    assert res["success"] is True
    assert res["total_clauses"] == 3
    results = res["clauses"]

    # Verify all 3 clauses returned without crashing
    assert results[0]["position"] == 1
    assert results[0]["severity"] in {"High", "Moderate", "Low", "Safe"}

    assert results[1]["position"] == 2
    assert results[1]["severity"] in {"High", "Moderate", "Low", "Safe"}  # Fallback applied cleanly

    assert results[2]["position"] == 3
    assert results[2]["severity"] in {"High", "Moderate", "Low", "Safe"}


def test_classified_clause_item_omits_numeric_risk_confidence():
    """Verify user-facing classified clause output omits numeric confidence risk score."""
    clauses = [
        {"position": 1, "clause_id": "1", "text": "Company indemnifies customer for all losses."}
    ]
    rule_findings = [
        {"rule_id": "R006", "risk_signal": "Broad Indemnification", "clause_id": "1"}
    ]

    res = classify_document_clauses_risk(clauses, rule_findings=rule_findings)
    clause_item = res["clauses"][0]

    assert "severity" in clause_item
    assert clause_item["severity"] in {"High", "Moderate", "Low", "Safe"}
    # Assert rule findings preserved unaltered
    assert len(clause_item["rule_findings"]) == 1
    assert clause_item["rule_findings"][0]["rule_id"] == "R006"

    # Assert no numeric confidence score field in user payload item
    assert "confidence" not in clause_item
    assert "score" not in clause_item


def test_classify_document_risk_api_endpoint():
    payload = {
        "clauses": [
            {"position": 1, "clause_id": "1", "text": "Party A disclaims all warranties."}
        ],
        "rule_findings": [
            {"rule_id": "R005", "risk_signal": "Excessive Liability Transfer", "clause_id": "1"}
        ]
    }
    response = client.post("/api/v1/classify-document-risk", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_clauses"] == 1
    assert data["clauses"][0]["severity"] in {"High", "Moderate", "Low", "Safe"}
    assert len(data["clauses"][0]["rule_findings"]) == 1
