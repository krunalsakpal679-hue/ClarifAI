"""
Legal-BERT Risk Classification Service Unit Tests
"""

import pytest
from app.services.risk_service import (
    get_legal_bert_model_name,
    get_legal_bert_status,
    classify_clause_risk,
    APPROVED_SEVERITY_LABELS
)


def test_legal_bert_model_name():
    name = get_legal_bert_model_name()
    assert "legal-bert" in name.lower()


def test_legal_bert_status():
    status = get_legal_bert_status()
    assert status["loaded"] is True
    assert status["num_labels"] == 4
    assert set(status["approved_severities"]) == {"High", "Moderate", "Low", "Safe"}
    assert status["is_interim_placeholder"] is True
    assert status["fine_tuned_status"] == "IMPLEMENTATION DECISION REQUIRED"


def test_classify_clause_risk_multiple_clauses():
    test_clauses = [
        "This Agreement shall automatically renew for additional 1-year terms unless notice is given 30 days prior.",
        "Either party may terminate this agreement at any time for convenience upon 60 days written notice.",
        "The Vendor disclaims all warranties, express or implied, including fitness for a particular purpose."
    ]

    for clause in test_clauses:
        res = classify_clause_risk(clause)
        
        # Verify severity is strictly one of the 4 approved values
        assert res["severity"] in {"High", "Moderate", "Low", "Safe"}
        assert res["logits_shape"] == [1, 4]
        assert 0.0 <= res["confidence"] <= 1.0
        assert res["latency_ms"] > 0.0
        assert res["is_interim_placeholder"] is True


def test_classify_clause_risk_with_rule_findings():
    clause = "This Agreement automatically renews each year unless terminated."
    rule_findings = [{"rule_id": "R001", "name": "Auto Renewal Detector"}]

    res = classify_clause_risk(clause, rule_findings=rule_findings)
    assert res["severity"] in {"High", "Moderate", "Low", "Safe"}
    assert res["rule_findings_included"] is True
