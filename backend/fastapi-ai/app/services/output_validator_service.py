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


# Fixed Rule Severity Mapping for R001-R015 (PRD Chapter 16.7)
RULE_SEVERITY_MAPPING: Dict[str, str] = {
    "R001": "Moderate",  # Auto-Renewal
    "R002": "High",      # Early-Termination Penalty
    "R003": "Moderate",  # Hidden/Add-on Charges
    "R004": "Moderate",  # Late-Payment Penalty
    "R005": "High",      # Excessive Liability Transfer
    "R006": "High",      # Broad Indemnification
    "R007": "High",      # Unilateral Modification
    "R008": "High",      # Unfavorable Termination
    "R009": "Moderate",  # Unusual Notice Requirement
    "R010": "Moderate",  # Restrictive Confidentiality
    "R011": "High",      # Broad IP Transfer
    "R012": "High",      # Arbitration/Dispute Restriction
    "R013": "Moderate",  # Data/Privacy Obligation
    "R014": "High",      # Restrictive Employment/Business Obligation (Non-compete)
    "R015": "High",      # Uncapped Liability Carve-Out
}

SEVERITY_ORDER: Dict[str, int] = {"Safe": 0, "Low": 1, "Moderate": 2, "High": 3}


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
    2. Principled Aggregation Precedence:
       - Deterministic rule findings (R001-R015) take precedence on pattern matches.
       - Legal-BERT catches general risks and elevates severity if model indicates higher risk.
       - Explains source explicitly (RULE_PRECEDENCE, AGREED, or MODEL_CLASSIFICATION).
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
    category = clause.get("category")
    categories = clause.get("categories", [])

    if not raw_classification or not isinstance(raw_classification, dict):
        logger.error(f"Clause {clause_id} output validation REJECTED: missing or malformed classifier dict.")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "category": category,
            "categories": categories,
            "final_severity": None,
            "validation_status": "FAILED_VALIDATION",
            "error_reason": MALFORMED_OUTPUT_REJECTED,
            "rule_findings": clause_rule_findings,
            "risk_source": "FAILED_VALIDATION",
            "risk_reason": "Risk classification unavailable due to malformed output."
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
            "category": category,
            "categories": categories,
            "final_severity": None,
            "validation_status": "FAILED_VALIDATION",
            "error_reason": error_code,
            "rule_findings": clause_rule_findings,
            "risk_source": "FAILED_VALIDATION",
            "risk_reason": f"Risk classification failed: {raw_error}"
        }

    try:
        model_severity = validate_severity_label(raw_severity)

        # Calculate maximum severity from deterministic rule findings (if any fired)
        rule_sevs = [
            RULE_SEVERITY_MAPPING[rf["rule_id"]]
            for rf in clause_rule_findings
            if rf.get("rule_id") in RULE_SEVERITY_MAPPING
        ]
        max_rule_sev = max(rule_sevs, key=lambda s: SEVERITY_ORDER.get(s, 0)) if rule_sevs else None

        # Principled Risk Aggregation Precedence:
        if max_rule_sev is not None:
            rule_signals_str = ", ".join(
                f"{rf.get('risk_signal', 'Risk Pattern')} ({rf.get('rule_id', '')})"
                for rf in clause_rule_findings if "rule_id" in rf
            )
            rule_ids_str = ", ".join(rf.get("rule_id", "") for rf in clause_rule_findings if "rule_id" in rf)

            if SEVERITY_ORDER[max_rule_sev] > SEVERITY_ORDER[model_severity]:
                final_severity = max_rule_sev
                risk_source = "RULE_PRECEDENCE"
                risk_reason = f"Severity determined by deterministic rule engine match: {rule_signals_str} taking precedence over Legal-BERT ({model_severity})."
            elif SEVERITY_ORDER[max_rule_sev] == SEVERITY_ORDER[model_severity]:
                final_severity = model_severity
                risk_source = "AGREED"
                risk_reason = f"Deterministic rule match ({rule_ids_str}) and Legal-BERT model agreed on {model_severity} severity."
            else:
                final_severity = model_severity
                risk_source = "MODEL_CLASSIFICATION"
                risk_reason = f"Severity determined by Legal-BERT classification ({model_severity}) elevating beyond rule finding ({max_rule_sev})."
        else:
            final_severity = model_severity
            risk_source = "MODEL_CLASSIFICATION"
            risk_reason = f"Severity determined by Legal-BERT classification ({model_severity}) based on contextual clause language."

        logger.info(f"Clause {clause_id} output validation PASSED: severity='{final_severity}' (source='{risk_source}'), rule_findings={len(clause_rule_findings)}.")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "category": category,
            "categories": categories,
            "final_severity": final_severity,
            "validation_status": "VALIDATED",
            "error_reason": None,
            "rule_findings": clause_rule_findings,
            "risk_source": risk_source,
            "risk_reason": risk_reason
        }

    except OutputValidationError as e:
        logger.error(f"Clause {clause_id} output validation REJECTED: {e.message}")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "category": category,
            "categories": categories,
            "final_severity": None,
            "validation_status": "FAILED_VALIDATION",
            "error_reason": e.code,
            "rule_findings": clause_rule_findings,
            "risk_source": "FAILED_VALIDATION",
            "risk_reason": f"Risk classification output rejected: {e.message}"
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
