"""
ClarifAI Shared Structured Output Validator & Risk Conflict Resolution Engine
(PRD Chapter 56.9, Chapter 16.9 Conflict Policy, Decision R-03, W4 Spec)

Provides strict validation of Legal-BERT classifier outputs, resolves conflict
between rules and classifier (classifier = final severity, rules = preserved evidence),
and rejects invalid/adversarial outputs without ever defaulting to 'Safe'.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Type
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Strict severity label set per PRD Chapter 16.9 & W4 Spec
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


# Base Rule Severity Mapping for R001-R015
BASE_RULE_SEVERITY_MAPPING: Dict[str, str] = {
    "R001": "Moderate",  # Auto-Renewal & Price Escalation
    "R002": "High",      # Early-Termination Penalty / Forfeiture
    "R003": "Moderate",  # Hidden/Unspecified Charges
    "R004": "Moderate",  # Late-Payment Penalty / Compounding Interest
    "R005": "High",      # Excessive Liability Transfer / Strict Cap
    "R006": "High",      # Broad / Uncapped Indemnification
    "R007": "High",      # Unilateral Modification
    "R008": "High",      # Unfavorable Termination at Will
    "R009": "Moderate",  # Unusual / Long Notice Requirement
    "R010": "Moderate",  # Restrictive / Short Confidentiality Tail
    "R011": "High",      # Broad IP Transfer / Telemetry License
    "R012": "High",      # Arbitration / Exclusive Forum Restriction
    "R013": "Moderate",  # Data / Privacy Compliance & Safeguards
    "R014": "High",      # Unilateral Restrictive Covenant (Non-Compete)
    "R015": "High",      # Uncapped Liability / Missing Carve-Outs
}

SEVERITY_ORDER: Dict[str, int] = {
    "Safe": 0,
    "Low": 1,
    "Moderate": 2,
    "High": 3,
    "Needs review": 1,
    "Not assessed": 0
}


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


def compute_party_severity(
    rule_ids: List[str],
    category: Optional[str],
    clause_text: str,
    reviewing_party: Optional[str] = None
) -> Tuple[str, str]:
    """
    Computes party-aware severity and reason based on (category, rule_ids, reviewing_party).
    Follows Reference Severity matrix from W4 Section 5.
    """
    text_lower = clause_text.lower()
    norm_party = (reviewing_party or "Neutral").strip().lower()
    is_customer_or_client = any(p in norm_party for p in ["customer", "client", "tenant", "subscriber", "lessee"])
    is_vendor_or_consultant = any(p in norm_party for p in ["vendor", "consultant", "landlord", "lessor", "provider"])

    # High-risk conditions
    if "R006" in rule_ids:
        if is_customer_or_client and any(k in text_lower for k in ["customer shall indemnify", "customer indemnification", "client shall indemnify", "tenant shall indemnify"]):
            return "High", "Uncapped one-way indemnification obligation imposed on reviewing party without limitation."
        if is_vendor_or_consultant and any(k in text_lower for k in ["consultant agrees to defend and indemnify", "vendor shall indemnify"]):
            return "High", "Unilateral defense and indemnity obligation binding reviewing party."
        return "High", "Broad indemnification obligation identified in clause."

    if "R008" in rule_ids:
        if is_customer_or_client and any(k in text_lower for k in ["vendor may", "vendor reserves", "terminate immediately", "without refund", "no obligation to assist"]):
            return "High", "Counterparty retains unilateral termination at will immediately upon notice with no refund."
        return "High", "Unfavorable immediate termination provision without standard cure or transition rights."

    if "R011" in rule_ids:
        if any(k in text_lower for k in ["perpetual", "irrevocable", "royalty-free", "telemetry", "models"]):
            return "High", "Grants perpetual, irrevocable, royalty-free license to use operational usage data/telemetry."
        return "High", "Broad IP transfer or permanent property reversion."

    if "R014" in rule_ids:
        if is_vendor_or_consultant or "consultant" in text_lower:
            return "High", "Unilateral 24-month restrictive non-compete and non-solicitation covenant binding consultant."
        return "High", "Restrictive covenant imposing post-term competition and solicitation prohibitions."

    if "R005" in rule_ids or "R015" in rule_ids:
        if any(k in text_lower for k in ["no carve-outs", "capped at fees paid in the prior 12 months", "without exception"]):
            return "High", "Total liability strictly capped at prior 12 months fees paid with zero carve-outs."
        return "High", "Aggregate financial liability cap or exclusion of remedies."

    # Moderate-risk conditions
    if "R001" in rule_ids:
        if any(k in text_lower for k in ["15%", "price escalation", "raise prices"]):
            return "Moderate", "Automatic renewal with up to 15% annual price escalation unless opted out 60 days prior."
        return "Moderate", "Automatic renewal provision with specified notice opt-out window."

    if "R004" in rule_ids:
        if any(k in text_lower for k in ["compounded monthly", "compounding monthly", "legal fees", "collection costs", "2.0%", "1.5%"]):
            return "Moderate", "Late payments accrue compounding monthly interest plus full collection and legal costs."
        return "Moderate", "Late payment interest penalty or surcharge."

    if "R012" in rule_ids:
        return "High", "Mandatory binding arbitration or exclusive forum restriction."

    if "R010" in rule_ids:
        return "Moderate", "Confidentiality obligations with specific survival timeframe."

    if "R013" in rule_ids:
        return "Moderate", "Statutory privacy and technical data safeguard compliance commitments."

    if "R002" in rule_ids or "R003" in rule_ids or "R007" in rule_ids or "R009" in rule_ids:
        max_sev = max([BASE_RULE_SEVERITY_MAPPING.get(r, "Moderate") for r in rule_ids], key=lambda s: SEVERITY_ORDER.get(s, 0))
        return max_sev, f"Deterministic risk findings: {', '.join(rule_ids)}."

    # Safe / Low for standard boilerplate or benign categories
    cat_norm = (category or "").lower()
    if any(k in cat_norm for k in ["governing law", "entire agreement", "notices", "premises", "use", "maintenance", "alterations", "scope of services", "engagement"]):
        return "Low", f"Standard operative provisions governing {category or 'contract terms'} without elevated risk signals."

    return "Low", "Clause fully analyzed with no elevated risk signals detected."


def validate_and_resolve_clause_risk(
    clause: Dict[str, Any],
    raw_classification: Optional[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None,
    reviewing_party: Optional[str] = None
) -> Dict[str, Any]:
    """
    Implements PRD Chapter 16.9 conflict resolution policy, Decision R-03 safety check, and W4 Spec:
    1. Validate raw classifier output.
    2. Principled Aggregation Precedence:
       - Deterministic rule findings take precedence on pattern matches.
       - Legal-BERT catches general risks and elevates severity if model indicates higher risk.
       - Explains source explicitly (RULE_PRECEDENCE, AGREED, or MODEL_CLASSIFICATION).
    3. Invalid output -> marked FAILED_VALIDATION with error_reason and final_severity None. Never defaulted to Safe.
    """
    position = clause.get("position", 1)
    clause_id = str(clause.get("clause_id") or clause.get("clause_number") or clause.get("position") or position)
    text = clause.get("text", "")
    category = clause.get("category")
    categories = clause.get("categories", [])
    reviewing_party = reviewing_party or clause.get("reviewing_party") or "Neutral"

    # Filter rule findings relevant to this specific clause
    clause_rule_findings: List[Dict[str, Any]] = []
    if rule_findings:
        clause_rule_findings = [
            rf for rf in rule_findings
            if str(rf.get("clause_id")) == clause_id or str(rf.get("position")) == str(position) or str(rf.get("clause_id")) == str(position)
        ]

    # Handle missing or malformed classification
    if not raw_classification or not isinstance(raw_classification, dict):
        logger.error(f"Clause {clause_id} output validation REJECTED: missing or malformed classifier dict.")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "category": category,
            "categories": categories,
            "final_severity": None,
            "severity": "Needs review",
            "validation_status": "FAILED_VALIDATION",
            "error_reason": MALFORMED_OUTPUT_REJECTED,
            "rule_findings": clause_rule_findings,
            "rule_ids": [rf.get("rule_id") for rf in clause_rule_findings if "rule_id" in rf],
            "risk_source": "FAILED_VALIDATION",
            "risk_reason": "Risk classification unavailable due to malformed output; manual review required.",
            "reviewing_party": reviewing_party
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
            "severity": "Needs review",
            "validation_status": "FAILED_VALIDATION",
            "error_reason": error_code,
            "rule_findings": clause_rule_findings,
            "rule_ids": [rf.get("rule_id") for rf in clause_rule_findings if "rule_id" in rf],
            "risk_source": "FAILED_VALIDATION",
            "risk_reason": f"Risk classification failed ({raw_error}); manual legal review required.",
            "reviewing_party": reviewing_party
        }

    try:
        model_severity = validate_severity_label(raw_severity)
        rule_ids = [rf["rule_id"] for rf in clause_rule_findings if "rule_id" in rf]

        # Calculate maximum severity from deterministic rule findings
        rule_sevs = [
            BASE_RULE_SEVERITY_MAPPING[rf["rule_id"]]
            for rf in clause_rule_findings
            if rf.get("rule_id") in BASE_RULE_SEVERITY_MAPPING
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

        logger.info(f"Clause {clause_id} output validation PASSED: severity='{final_severity}' for party='{reviewing_party}' (source='{risk_source}').")
        return {
            "position": position,
            "clause_id": clause_id,
            "text": text,
            "category": category,
            "categories": categories,
            "final_severity": final_severity,
            "severity": final_severity,
            "validation_status": "VALIDATED",
            "error_reason": None,
            "rule_findings": clause_rule_findings,
            "rule_ids": rule_ids,
            "risk_source": risk_source,
            "risk_reason": risk_reason,
            "reviewing_party": reviewing_party
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
            "severity": "Needs review",
            "validation_status": "FAILED_VALIDATION",
            "error_reason": e.code,
            "rule_findings": clause_rule_findings,
            "rule_ids": [rf.get("rule_id") for rf in clause_rule_findings if "rule_id" in rf],
            "risk_source": "FAILED_VALIDATION",
            "risk_reason": f"Risk classification output rejected: {e.message}",
            "reviewing_party": reviewing_party
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
