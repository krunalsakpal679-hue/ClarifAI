"""
ClarifAI Shared Structured Output Validator & Risk Conflict Resolution Engine
(PRD Chapter 56.9, Chapter 16.9 Conflict Policy, Decision R-03)

Provides strict validation of Legal-BERT classifier outputs, resolves conflict
between rules and classifier (classifier = final severity, rules = preserved evidence),
and rejects invalid/adversarial outputs without ever defaulting to 'Safe'.
"""

import logging
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Strict 4-level severity label set per PRD Chapter 16.9
APPROVED_SEVERITY_SET = {"High", "Moderate", "Low", "Safe"}

# Domain Error Codes for Output Validation
INVALID_SEVERITY_REJECTED = "INVALID_SEVERITY_REJECTED"
MALFORMED_OUTPUT_REJECTED = "MALFORMED_OUTPUT_REJECTED"
CLASSIFICATION_TIMEOUT = "CLASSIFICATION_TIMEOUT"
RUNTIME_ERROR_REJECTED = "RUNTIME_ERROR_REJECTED"


class OutputValidationError(Exception):
    """Raised when an AI structured output fails validation checks."""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def validate_severity_label(severity: Any) -> str:
    """
    Validates that a severity value is a string and belongs to APPROVED_SEVERITY_SET.
    Raises OutputValidationError if invalid.
    """
    if not isinstance(severity, str):
        logger.warning("Output validation rejected non-string severity label.")
        raise OutputValidationError(
            code=INVALID_SEVERITY_REJECTED,
            message=f"Severity label must be a string, got {type(severity).__name__}."
        )

    clean_severity = severity.strip().capitalize()
    if clean_severity not in APPROVED_SEVERITY_SET:
        logger.warning(f"Output validation rejected unapproved severity label: '{severity}'.")
        raise OutputValidationError(
            code=INVALID_SEVERITY_REJECTED,
            message=f"Severity '{severity}' is outside approved set {sorted(list(APPROVED_SEVERITY_SET))}."
        )

    return clean_severity


def validate_and_resolve_clause_risk(
    clause: Dict[str, Any],
    raw_classification: Optional[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Implements PRD Chapter 16.9 conflict resolution policy & Decision R-03 safety check:
    1. Validate raw classifier output.
    2. Valid output -> becomes clause final_severity. Rule findings attached as preserved evidence.
    3. Invalid output -> marked FAILED_VALIDATION with error_reason. NEVER converted to Safe.
    """
    position = clause.get("position", 1)
    clause_id = str(clause.get("clause_id") or clause.get("position") or position)
    text = clause.get("text", "")

    # Filter rule findings relevant to this specific clause
    clause_rule_findings: List[Dict[str, Any]] = []
    if rule_findings:
        clause_rule_findings = [
            rf for rf in rule_findings
            if str(rf.get("clause_id")) == clause_id or str(rf.get("position")) == clause_id
        ]

    # Validate Raw Classification Output
    if not raw_classification or not isinstance(raw_classification, dict):
        logger.error(f"Clause {clause_id} output validation REJECTED: missing or malformed classifier dict.")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "final_severity": None,
            "validation_status": "FAILED_VALIDATION",
            "error_reason": MALFORMED_OUTPUT_REJECTED,
            "rule_findings": clause_rule_findings
        }

    raw_severity = raw_classification.get("severity")
    raw_error = raw_classification.get("error")

    # Check for classifier execution timeout or runtime error
    if raw_error:
        raw_err_str = str(raw_error).lower()
        error_code = CLASSIFICATION_TIMEOUT if any(k in raw_err_str for k in ["timeout", "timed out", "time out"]) else RUNTIME_ERROR_REJECTED
        logger.error(f"Clause {clause_id} output validation REJECTED due to classifier error: {raw_error}")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "final_severity": None,
            "validation_status": "FAILED_VALIDATION",
            "error_reason": error_code,
            "rule_findings": clause_rule_findings
        }

    try:
        validated_severity = validate_severity_label(raw_severity)
        logger.info(f"Clause {clause_id} output validation PASSED: severity='{validated_severity}', rule_findings={len(clause_rule_findings)}.")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "final_severity": validated_severity,
            "validation_status": "VALIDATED",
            "error_reason": None,
            "rule_findings": clause_rule_findings
        }

    except OutputValidationError as e:
        logger.error(f"Clause {clause_id} output validation REJECTED: {e.message}")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "final_severity": None,
            "validation_status": "FAILED_VALIDATION",
            "error_reason": e.code,
            "rule_findings": clause_rule_findings
        }


def validate_structured_output(
    data: Dict[str, Any],
    schema_class: Type[BaseModel]
) -> Dict[str, Any]:
    """
    Shared reusable structured output validator for Pydantic models (Chapter 56.9).
    Can be called by downstream phases (simplification, chatbot, comparison).
    """
    try:
        validated_instance = schema_class(**data)
        return validated_instance.model_dump()
    except ValidationError as ve:
        logger.error(f"Structured output schema validation failed for {schema_class.__name__}: {ve.errors()}")
        raise OutputValidationError(
            code="SCHEMA_VALIDATION_FAILED",
            message=f"Structured output failed {schema_class.__name__} schema validation.",
            details={"errors": ve.errors()}
        ) from ve
