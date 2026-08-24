"""
Adversarial Unit Tests for AI-PHASE-RISK-OUTPUT-VALIDATION
(PRD Chapter 56.9, Chapter 16.9 Conflict Policy, Decision R-03 Safety Rule)

Tests 100% of invalid output categories (out-of-enum, missing, malformed, timeout,
runtime error, corrupted result), conflict preservation policy, Decision R-03 prohibition
of defaulting to Safe, and shared reusable validator functions.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.main import app
from app.services.output_validator_service import (
    validate_severity_label,
    validate_and_resolve_clause_risk,
    validate_structured_output,
    OutputValidationError,
    INVALID_SEVERITY_REJECTED,
    MALFORMED_OUTPUT_REJECTED,
    CLASSIFICATION_TIMEOUT,
    RUNTIME_ERROR_REJECTED
)

client = TestClient(app)


def test_validate_severity_label_valid_cases():
    for valid_label in ["High", "Moderate", "Low", "Safe", "high", "moderate ", "LOW"]:
        assert validate_severity_label(valid_label) in {"High", "Moderate", "Low", "Safe"}


def test_validate_severity_label_out_of_enum_adversarial_rejection():
    """Adversarial test: out-of-enum severity labels are rejected."""
    invalid_labels = ["Critical", "Uncertain", "Extreme", "Medium", "123", "", "   ", None, 99]
    for invalid in invalid_labels:
        with pytest.raises(OutputValidationError) as exc_info:
            validate_severity_label(invalid)
        assert exc_info.value.code == INVALID_SEVERITY_REJECTED


def test_conflict_preservation_policy():
    """
    Chapter 16.9: Valid classifier result becomes final severity.
    Conflicting rule findings are PRESERVED as supporting evidence — never override and never discarded.
    """
    clause = {"position": 1, "clause_id": "1", "text": "Customer assumes liability."}
    raw_classification = {"severity": "Low", "confidence": 0.85}
    rule_findings = [
        {"rule_id": "R005", "risk_signal": "Excessive Liability Transfer", "clause_id": "1"}
    ]

    res = validate_and_resolve_clause_risk(
        clause=clause,
        raw_classification=raw_classification,
        rule_findings=rule_findings
    )

    assert res["validation_status"] == "VALIDATED"
    assert res["final_severity"] == "Low"  # Classifier result is final severity
    assert res["error_reason"] is None

    # Assert rule finding is preserved unaltered as evidence
    assert len(res["rule_findings"]) == 1
    assert res["rule_findings"][0]["rule_id"] == "R005"
    assert res["rule_findings"][0]["risk_signal"] == "Excessive Liability Transfer"


def test_decision_r03_safety_never_default_invalid_to_safe():
    """
    Decision R-03: An invalid classifier output must be REJECTED and marked FAILED_VALIDATION.
    It must NEVER be silently converted to 'Safe'.
    """
    clause = {"position": 2, "clause_id": "2", "text": "Ambiguous clause text."}
    invalid_classification = {"severity": "Uncertain"}  # Out-of-enum

    res = validate_and_resolve_clause_risk(
        clause=clause,
        raw_classification=invalid_classification
    )

    assert res["validation_status"] == "FAILED_VALIDATION"
    assert res["final_severity"] is None  # MUST NOT BE 'Safe'
    assert res["error_reason"] == INVALID_SEVERITY_REJECTED


def test_missing_output_category_rejection():
    """Missing or None classifier dict output is rejected."""
    clause = {"position": 3, "clause_id": "3", "text": "Some text."}

    res = validate_and_resolve_clause_risk(clause=clause, raw_classification=None)
    assert res["validation_status"] == "FAILED_VALIDATION"
    assert res["final_severity"] is None
    assert res["error_reason"] == MALFORMED_OUTPUT_REJECTED


def test_malformed_output_category_rejection():
    """Non-dict classifier output is rejected."""
    clause = {"position": 4, "clause_id": "4", "text": "Some text."}

    for malformed in ["not a dict", [1, 2, 3], 12345]:
        res = validate_and_resolve_clause_risk(clause=clause, raw_classification=malformed)
        assert res["validation_status"] == "FAILED_VALIDATION"
        assert res["final_severity"] is None
        assert res["error_reason"] == MALFORMED_OUTPUT_REJECTED


def test_timeout_error_category_rejection():
    """Classifier timeout error is rejected with CLASSIFICATION_TIMEOUT code."""
    clause = {"position": 5, "clause_id": "5", "text": "Heavy clause."}
    timeout_raw = {"error": "Classifier inference timed out after 30 seconds."}

    res = validate_and_resolve_clause_risk(clause=clause, raw_classification=timeout_raw)
    assert res["validation_status"] == "FAILED_VALIDATION"
    assert res["final_severity"] is None
    assert res["error_reason"] == CLASSIFICATION_TIMEOUT


def test_runtime_error_category_rejection():
    """Classifier runtime error is rejected with RUNTIME_ERROR_REJECTED code."""
    clause = {"position": 6, "clause_id": "6", "text": "Corrupted clause."}
    runtime_raw = {"error": "PyTorch CUDA out of memory runtime error."}

    res = validate_and_resolve_clause_risk(clause=clause, raw_classification=runtime_raw)
    assert res["validation_status"] == "FAILED_VALIDATION"
    assert res["final_severity"] is None
    assert res["error_reason"] == RUNTIME_ERROR_REJECTED


def test_shared_validator_pydantic_schema_validation():
    """Chapter 56.9: Shared reusable structured output validator for Pydantic models."""
    class DummySchema(BaseModel):
        name: str
        value: int = Field(..., ge=0)

    # Valid data
    valid_dict = {"name": "Test", "value": 42}
    res = validate_structured_output(valid_dict, DummySchema)
    assert res["name"] == "Test"
    assert res["value"] == 42

    # Invalid data raises OutputValidationError
    invalid_dict = {"name": "Test", "value": -5}
    with pytest.raises(OutputValidationError) as exc_info:
        validate_structured_output(invalid_dict, DummySchema)
    assert exc_info.value.code == "SCHEMA_VALIDATION_FAILED"


def test_validate_risk_output_api_endpoint():
    """API endpoint test for POST /api/v1/validate-risk-output."""
    payload = {
        "clause": {"position": 1, "clause_id": "1", "text": "Vendor disclaims all warranties."},
        "raw_classification": {"severity": "High"},
        "rule_findings": [{"rule_id": "R005", "risk_signal": "Excessive Liability Transfer", "clause_id": "1"}]
    }

    response = client.post("/api/v1/validate-risk-output", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    result = data["result"]
    assert result["validation_status"] == "VALIDATED"
    assert result["final_severity"] == "High"
    assert len(result["rule_findings"]) == 1
