"""
Principled Risk Aggregation Precedence Unit Tests (Phase 2 Part 3)
Verifies:
1. Rule precedence: Deterministic rule match takes precedence over under-predicting Legal-BERT model.
2. Agreement: Deterministic rule match and Legal-BERT model agreed on severity.
3. Model classification: Legal-BERT contextual classification when no rule fires or model elevates severity.
4. Structured reason explicitly documents the aggregation source in risk.reason.
"""

import pytest
from app.services.output_validator_service import validate_and_resolve_clause_risk


def test_rule_precedence_over_underpredicting_model():
    """
    Test Case 1: A deterministic High-risk rule (R005 Excessive Liability Transfer) fires,
    while Legal-BERT produces 'Low' severity.
    Principled precedence: Rule takes precedence -> final_severity = 'High', source = 'RULE_PRECEDENCE'.
    """
    clause = {
        "position": 1,
        "clause_id": "c-001",
        "text": "Customer assumes all liability and user assumes all risk for any software defects.",
        "category": "Liability"
    }
    raw_classification = {"severity": "Low", "confidence": 0.82}
    rule_findings = [
        {"rule_id": "R005", "risk_signal": "Excessive Liability Transfer", "clause_id": "c-001"}
    ]

    res = validate_and_resolve_clause_risk(
        clause=clause,
        raw_classification=raw_classification,
        rule_findings=rule_findings
    )

    assert res["validation_status"] == "VALIDATED"
    assert res["final_severity"] == "High"
    assert res["risk_source"] == "RULE_PRECEDENCE"
    assert "taking precedence over Legal-BERT (Low)" in res["risk_reason"]
    assert len(res["rule_findings"]) == 1


def test_rule_and_model_agreement():
    """
    Test Case 2: A deterministic High-risk rule (R006 Broad Indemnification) fires,
    and Legal-BERT also outputs 'High' severity.
    Principled precedence: Both agree -> final_severity = 'High', source = 'AGREED'.
    """
    clause = {
        "position": 2,
        "clause_id": "c-002",
        "text": "Provider shall unconditionally defend, indemnify, and hold harmless Customer against any and all claims.",
        "category": "Liability"
    }
    raw_classification = {"severity": "High", "confidence": 0.94}
    rule_findings = [
        {"rule_id": "R006", "risk_signal": "Broad Indemnification", "clause_id": "c-002"}
    ]

    res = validate_and_resolve_clause_risk(
        clause=clause,
        raw_classification=raw_classification,
        rule_findings=rule_findings
    )

    assert res["validation_status"] == "VALIDATED"
    assert res["final_severity"] == "High"
    assert res["risk_source"] == "AGREED"
    assert "and Legal-BERT model agreed on High severity" in res["risk_reason"]


def test_model_classification_without_rule_findings():
    """
    Test Case 3: No rule fires, but Legal-BERT classifies clause as 'Moderate' risk.
    Principled precedence: Model classification -> final_severity = 'Moderate', source = 'MODEL_CLASSIFICATION'.
    """
    clause = {
        "position": 3,
        "clause_id": "c-003",
        "text": "Customer shall allow vendor reasonable access to its IT facilities during off-peak hours for maintenance.",
        "category": "Renewal"
    }
    raw_classification = {"severity": "Moderate", "confidence": 0.76}
    rule_findings = []

    res = validate_and_resolve_clause_risk(
        clause=clause,
        raw_classification=raw_classification,
        rule_findings=rule_findings
    )

    assert res["validation_status"] == "VALIDATED"
    assert res["final_severity"] == "Moderate"
    assert res["risk_source"] == "MODEL_CLASSIFICATION"
    assert "Severity determined by Legal-BERT classification (Moderate)" in res["risk_reason"]


def test_moderate_rule_precedence_over_safe_model():
    """
    Test Case 4: A deterministic Moderate-risk rule (R004 Late-Payment Penalty) fires,
    while Legal-BERT produces 'Safe'.
    Principled precedence: Rule takes precedence -> final_severity = 'Moderate', source = 'RULE_PRECEDENCE'.
    """
    clause = {
        "position": 4,
        "clause_id": "c-004",
        "text": "Late payments shall accrue late payment interest at the rate of 2% per month.",
        "category": "Payment"
    }
    raw_classification = {"severity": "Safe", "confidence": 0.88}
    rule_findings = [
        {"rule_id": "R004", "risk_signal": "Late-Payment Penalty", "clause_id": "c-004"}
    ]

    res = validate_and_resolve_clause_risk(
        clause=clause,
        raw_classification=raw_classification,
        rule_findings=rule_findings
    )

    assert res["validation_status"] == "VALIDATED"
    assert res["final_severity"] == "Moderate"
    assert res["risk_source"] == "RULE_PRECEDENCE"
    assert "Late-Payment Penalty (R004)" in res["risk_reason"]
