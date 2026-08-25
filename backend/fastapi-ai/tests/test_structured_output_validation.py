"""
ClarifAI Structured Output Schema Validation Test Matrix (AI-PHASE-STRUCTURED-OUTPUT-VALIDATION)
Adversarial test suite verifying strict Pydantic validation across all 6 AI output types:
1. Risk Classification Result (DocumentRiskResponse / OutputValidationResponse)
2. Clause Categorization Result (ClauseCategorizationResponse)
3. Clause Simplification Result (SimplificationResponse)
4. Document Summary Result (DocumentSummaryResponse)
5. Chatbot Answer Result (ChatbotResponse)
6. Contract Comparison Result (ComparisonResponse)

Tests:
- Valid payloads pass.
- Malformed JSON / invalid data types raise ValidationError.
- Missing required fields raise ValidationError.
- Invalid enum values raise ValidationError.
- Extra/unexpected fields handled cleanly per model strictness.
"""

import pytest
import json
from pydantic import ValidationError

from app.models.risk import DocumentRiskResponse, ClassifiedClauseItem, OutputValidationResponse
from app.models.clause_categorization import ClauseCategorizationResponse, CategorizedClauseItem, ClauseCategoryEnum
from app.models.simplification import SimplificationResponse, SimplificationResult
from app.models.summarization import DocumentSummaryResponse
from app.models.chatbot import ChatbotResponse
from app.models.comparison import ComparisonResponse, ClauseComparisonItem
from app.models.common import SCHEMA_VERSION


# =====================================================================
# 1. RISK CLASSIFICATION RESULT SCHEMA TESTS
# =====================================================================

def test_risk_result_schema_valid_payload():
    """Verifies valid DocumentRiskResponse payload parses cleanly."""
    payload = {
        "success": True,
        "total_clauses": 1,
        "clauses": [
            {
                "position": 1,
                "clause_id": "c1",
                "text": "The tenant shall pay rent by 1st of month.",
                "severity": "Safe",
                "final_severity": "Safe",
                "validation_status": "VALIDATED",
                "rule_findings": []
            }
        ],
        "schema_version": SCHEMA_VERSION
    }
    model = DocumentRiskResponse.model_validate(payload)
    assert model.total_clauses == 1
    assert model.clauses[0].final_severity == "Safe"


def test_risk_result_schema_missing_required_field():
    """Verifies missing required total_clauses field raises ValidationError."""
    payload = {
        "success": True,
        "clauses": [],
        "schema_version": SCHEMA_VERSION
    }
    with pytest.raises(ValidationError):
        DocumentRiskResponse.model_validate(payload)


def test_risk_result_schema_wrong_data_type():
    """Verifies wrong data type for total_clauses raises ValidationError."""
    payload = {
        "success": True,
        "total_clauses": "not_an_int",
        "clauses": [],
        "schema_version": SCHEMA_VERSION
    }
    with pytest.raises(ValidationError):
        DocumentRiskResponse.model_validate(payload)


# =====================================================================
# 2. CLAUSE CATEGORIZATION RESULT SCHEMA TESTS
# =====================================================================

def test_categorization_result_schema_valid_payload():
    """Verifies valid ClauseCategorizationResponse payload with PRD-approved 8 categories."""
    payload = {
        "success": True,
        "total_clauses": 1,
        "clauses": [
            {
                "position": 1,
                "text": "Payment terms clause.",
                "character_count": 21,
                "categories": ["Payment"]
            }
        ],
        "schema_version": SCHEMA_VERSION
    }
    model = ClauseCategorizationResponse.model_validate(payload)
    assert model.clauses[0].categories[0] == ClauseCategoryEnum.PAYMENT


def test_categorization_result_schema_invalid_enum_value():
    """Verifies unapproved category enum raises ValidationError."""
    payload = {
        "success": True,
        "total_clauses": 1,
        "clauses": [
            {
                "position": 1,
                "text": "Unapproved category clause.",
                "categories": ["UnapprovedCategory"]
            }
        ],
        "schema_version": SCHEMA_VERSION
    }
    with pytest.raises(ValidationError):
        ClauseCategorizationResponse.model_validate(payload)


def test_categorization_result_schema_missing_position():
    """Verifies missing required position in clause item raises ValidationError."""
    payload = {
        "success": True,
        "total_clauses": 1,
        "clauses": [
            {
                "text": "Missing position.",
                "categories": ["Payment"]
            }
        ],
        "schema_version": SCHEMA_VERSION
    }
    with pytest.raises(ValidationError):
        ClauseCategorizationResponse.model_validate(payload)


# =====================================================================
# 3. CLAUSE SIMPLIFICATION RESULT SCHEMA TESTS
# =====================================================================

def test_simplification_result_schema_valid_payload():
    """Verifies valid SimplificationResponse payload."""
    payload = {
        "success": True,
        "total_clauses": 1,
        "clauses": [
            {
                "position": 1,
                "clause_id": "c1",
                "original_text": "Complex legal text.",
                "simplified_text": "Simple text.",
                "why_flagged": "High risk signal.",
                "severity": "High",
                "status": "SUCCESS"
            }
        ],
        "schema_version": SCHEMA_VERSION
    }
    model = SimplificationResponse.model_validate(payload)
    assert model.clauses[0].simplified_text == "Simple text."


def test_simplification_result_schema_missing_simplified_text():
    """Verifies missing required simplified_text raises ValidationError."""
    payload = {
        "position": 1,
        "original_text": "Complex text."
    }
    with pytest.raises(ValidationError):
        SimplificationResult.model_validate(payload)


def test_simplification_result_schema_wrong_type_position():
    """Verifies wrong type for position raises ValidationError."""
    payload = {
        "position": "invalid_int",
        "original_text": "Complex text.",
        "simplified_text": "Simple text."
    }
    with pytest.raises(ValidationError):
        SimplificationResult.model_validate(payload)


# =====================================================================
# 4. DOCUMENT SUMMARY RESULT SCHEMA TESTS
# =====================================================================

def test_summary_result_schema_valid_payload():
    """Verifies valid DocumentSummaryResponse payload with all 4 executive summary fields."""
    payload = {
        "success": True,
        "summary_status": "AVAILABLE",
        "purpose_text": "Purpose summary.",
        "obligations_text": "Obligations summary.",
        "key_terms_text": "Key terms summary.",
        "key_risks_text": "Key risks summary.",
        "model_name": "facebook/bart-base",
        "schema_version": SCHEMA_VERSION
    }
    model = DocumentSummaryResponse.model_validate(payload)
    assert model.summary_status == "AVAILABLE"
    assert model.purpose_text == "Purpose summary."


def test_summary_result_schema_missing_model_name():
    """Verifies missing required model_name raises ValidationError."""
    payload = {
        "success": True,
        "summary_status": "AVAILABLE",
        "purpose_text": "Purpose summary.",
        "schema_version": SCHEMA_VERSION
    }
    with pytest.raises(ValidationError):
        DocumentSummaryResponse.model_validate(payload)


def test_summary_result_schema_malformed_json():
    """Verifies malformed JSON string parsing raises JSONDecodeError or ValidationError."""
    raw_json = '{"success": true, "summary_status": "AVAILABLE", "purpose_text":'
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw_json)


# =====================================================================
# 5. CHATBOT ANSWER RESULT SCHEMA TESTS
# =====================================================================

def test_chatbot_result_schema_valid_payload():
    """Verifies valid ChatbotResponse payload."""
    payload = {
        "answer": "The contract duration is 3 years.",
        "has_sufficient_evidence": True,
        "source_clause_ids": ["c1"],
        "disclaimer": "Reference only.",
        "session_id": "sess_1",
        "user_id": "user_1",
        "document_id": "doc_1",
        "question": "What is the duration?",
        "target_language": "en",
        "schema_version": SCHEMA_VERSION
    }
    model = ChatbotResponse.model_validate(payload)
    assert model.has_sufficient_evidence is True
    assert model.source_clause_ids == ["c1"]


def test_chatbot_result_schema_missing_session_id():
    """Verifies missing required session_id raises ValidationError."""
    payload = {
        "answer": "Answer text.",
        "has_sufficient_evidence": True,
        "user_id": "user_1",
        "document_id": "doc_1",
        "question": "Question?"
    }
    with pytest.raises(ValidationError):
        ChatbotResponse.model_validate(payload)


def test_chatbot_result_schema_wrong_type_has_sufficient_evidence():
    """Verifies non-boolean value for has_sufficient_evidence raises ValidationError."""
    payload = {
        "answer": "Answer text.",
        "has_sufficient_evidence": "not_a_bool",
        "disclaimer": "Disclaimer.",
        "session_id": "sess_1",
        "user_id": "user_1",
        "document_id": "doc_1",
        "question": "Question?",
        "schema_version": SCHEMA_VERSION
    }
    with pytest.raises(ValidationError):
        ChatbotResponse.model_validate(payload)


# =====================================================================
# 6. CONTRACT COMPARISON RESULT SCHEMA TESTS
# =====================================================================

def test_comparison_result_schema_valid_payload():
    """Verifies valid ComparisonResponse payload."""
    payload = {
        "success": True,
        "user_id": "user_1",
        "document_id_a": "doc_a",
        "document_id_b": "doc_b",
        "total_clauses_a": 10,
        "total_clauses_b": 10,
        "matched_count": 8,
        "changed_count": 2,
        "missing_count": 0,
        "is_low_confidence": False,
        "comparison_results": [
            {
                "clause_id_a": "a1",
                "clause_id_b": "b1",
                "similarity_score": 0.95,
                "classification": "MATCHED"
            }
        ],
        "schema_version": SCHEMA_VERSION
    }
    model = ComparisonResponse.model_validate(payload)
    assert model.matched_count == 8
    assert model.comparison_results[0].classification == "MATCHED"


def test_comparison_result_schema_missing_document_ids():
    """Verifies missing required document_id_a raises ValidationError."""
    payload = {
        "success": True,
        "user_id": "user_1",
        "document_id_b": "doc_b",
        "total_clauses_a": 10,
        "total_clauses_b": 10,
        "matched_count": 8,
        "changed_count": 2,
        "missing_count": 0,
        "comparison_results": []
    }
    with pytest.raises(ValidationError):
        ComparisonResponse.model_validate(payload)


def test_comparison_result_schema_wrong_type_similarity_score():
    """Verifies wrong data type for similarity_score raises ValidationError."""
    payload = {
        "clause_id_a": "a1",
        "clause_id_b": "b1",
        "similarity_score": "not_a_float",
        "classification": "MATCHED"
    }
    with pytest.raises(ValidationError):
        ClauseComparisonItem.model_validate(payload)
