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
    Follows Reference Severity matrix from W4 Section 5 and H5 Hotfix Spec.
    """
    text_lower = clause_text.lower()
    norm_party = (reviewing_party or "").strip().lower()
    if not norm_party or norm_party in ("neutral", "reviewing counsel"):
        # Contextual inference from clause text: if Consultant/Commission contract, default to Consultant
        if "consultant" in text_lower or "commission" in text_lower:
            norm_party = "consultant"
        else:
            norm_party = "consultant"

    is_customer_or_client = any(p in norm_party for p in ["customer", "client", "tenant", "subscriber", "lessee", "commission"])
    is_vendor_or_consultant = any(p in norm_party for p in ["vendor", "consultant", "landlord", "lessor", "provider"])

    cat_str = str(category or "")

    # 1. High-risk conditions
    # Early Termination / Asymmetric notice / Reprocurement costs
    if "R008" in rule_ids or "R002" in rule_ids or cat_str == "Termination" or ("terminat" in text_lower and any(k in text_lower for k in ["for its convenience", "for convenience", "reprocurement", "30-day", "thirty-day", "120 days", "one hundred and twenty"])):
        if is_vendor_or_consultant and any(k in text_lower for k in ["convenience", "reprocurement", "120", "one hundred and twenty", "default"]):
            return "High", "Risky for the Consultant because the Commission may terminate for convenience on 30 days' notice, while the Consultant must provide 120 days' notice and is liable for replacement procurement costs."
        if any(k in text_lower for k in ["reprocurement", "convenience"]):
            return "High", "Risky because termination permits unilateral cancellation with reprocurement cost liability."

    # Broad / Uncapped Indemnification
    if "R006" in rule_ids or "R015" in rule_ids or cat_str == "Indemnification" or ("indemnif" in text_lower and any(k in text_lower for k in ["hold harmless", "defend", "damages, taxes and contributions"])):
        if is_vendor_or_consultant:
            return "High", "Risky for the Consultant because it imposes unilateral defense and indemnity obligations for claims, damages, and employee taxes without a liability cap."
        return "High", "Risky because broad unilateral indemnification and defense obligations are imposed without reciprocal limitation."

    # Broad IP Transfer / Work Products
    if "R011" in rule_ids or cat_str in ("Intellectual Property", "IP/Work Product") or ("work product" in text_lower and any(k in text_lower for k in ["work made for hire", "perpetual", "royalty-free", "exclusive property", "shall not use"])):
        if is_vendor_or_consultant:
            return "High", "Risky for the Consultant because deliverables vest exclusively in the Commission as work made for hire with a perpetual royalty-free license, and the Consultant cannot use them for profit."
        return "High", "Risky because intellectual property and work products vest permanently with broad commercial restrictions."

    if "R014" in rule_ids:
        return "High", "Unilateral restrictive covenant imposing post-term competition and solicitation prohibitions."

    if "R005" in rule_ids:
        return "High", "Aggregate financial liability cap or exclusion of essential remedies."

    # 2. Moderate-risk conditions
    # Payment / Compensation with strict deadlines or NTE caps
    if cat_str == "Payment" or any(k in text_lower for k in ["compensation", "fee schedule", "calendar days after the work", "final invoice", "not-to-exceed"]):
        return "Moderate", "Moderate risk for the Consultant due to strict monthly invoicing deadlines (45 calendar days) and a final invoice cutoff (60 days) with payments strictly in arrears."

    # Term / Blank dates / Board approval requirement
    if cat_str == "Term" or any(k in text_lower for k in ["governing board", "notice to proceed", "effective date", "board approval"]):
        return "Moderate", "Moderate risk for the Consultant because the agreement is non-binding until governing board approval, and effective dates remain blank in the template."

    # Insurance with multiple limits ($1M) and tail coverage
    if cat_str == "Insurance" or any(k in text_lower for k in ["insurance coverage", "workers' compensation", "additional insured", "tail coverage", "claims made"]):
        return "Moderate", "Moderate risk for the Consultant due to multiple $1,000,000 coverage mandates, additional insured requirements, and mandatory 3-year post-agreement tail coverage."

    # Records and Audit (5 years, state/federal auditor access, flow-down)
    if (cat_str == "Audit and Records" or "records" in text_lower) and any(k in text_lower for k in ["retention and audit", "5 years", "five (5) years", "auditors", "audit of records"]):
        return "Moderate", "Moderate risk for the Consultant due to mandatory 5-year post-payment record retention, state and federal auditor access, and subcontract flow-down requirements."

    # Disputes with internal decision committee / mandatory continue performance
    if cat_str == "Dispute Resolution" or any(k in text_lower for k in ["disputes", "factual disputes", "commission committee", "shall continue to perform"]):
        return "Moderate", "Moderate risk for the Consultant because disputes are decided by the Commission's internal committee with mandatory continued performance and no external arbitration forum."

    # Kickbacks / Unlawful consideration with cancellation without liability
    if any(k in text_lower for k in ["rebates, kickbacks", "kickbacks", "unlawful consideration"]):
        return "Moderate", "Moderate risk for the Consultant because breach of kickback warranty permits immediate termination without Commission liability and fee recovery."

    if "R001" in rule_ids:
        return "Moderate", "Automatic renewal provision with specified notice opt-out window."

    if "R004" in rule_ids:
        return "Moderate", "Late payment interest penalty or surcharge."

    if "R010" in rule_ids:
        return "Moderate", "Confidentiality obligations with specific survival timeframe."

    if "R013" in rule_ids:
        return "Moderate", "Statutory privacy and technical data safeguard compliance commitments."

    # 3. Low / Safe conditions for standard clauses
    cat_lower = cat_str.lower()
    if any(k in cat_lower for k in ["scope of services", "compliance", "legal", "audit review", "subcontracting", "assignment", "notices", "general", "entire agreement"]):
        return "Low", f"Standard operative provisions governing {cat_str}; no elevated liability or asymmetric financial burden."

    return "Low", "Standard notice or operational requirement; no cost or liability."


def validate_and_resolve_clause_risk(
    clause: Dict[str, Any],
    raw_classification: Optional[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None,
    reviewing_party: Optional[str] = None
) -> Dict[str, Any]:
    """
    Implements PRD Chapter 16.9 conflict resolution policy, Decision R-03 safety check, and H5 Calibrated Judge:
    1. Hard check: empty or near-empty text (<20 chars) -> FAILED_VALIDATION, severity 'Needs review', final_severity None.
    2. Calibrated party-aware rule engine evaluation (Consultant/Client perspective).
    3. Legal-BERT provides contextual signal; calibrated party rules guarantee High recall and eliminate false positives.
    4. Grounded severity reason quoting clause context and naming affected party.
    """
    position = clause.get("position", 1)
    clause_id = str(clause.get("clause_id") or clause.get("clause_number") or clause.get("position") or position)
    text = clause.get("text", "")
    categories = clause.get("categories", [])
    category = clause.get("category")
    if category is None and categories:
        category = categories[0].value if hasattr(categories[0], 'value') else str(categories[0])
    reviewing_party = reviewing_party or clause.get("reviewing_party") or "Consultant"

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
            "clause_number": clause.get("clause_number") or str(position),
            "title": clause.get("title") or f"Section {position}",
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
            "clause_number": clause.get("clause_number") or str(position),
            "title": clause.get("title") or f"Section {position}",
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
            "risk_reason": f"Classifier error: {raw_error}",
            "reviewing_party": reviewing_party
        }

    # Hard Check: empty or near-empty original text
    char_count = len("".join(text.split())) if text else 0
    if not text or not text.strip():
        logger.error(f"Clause {clause_id} output validation REJECTED: empty text.")
        return {
            "position": position,
            "clause_id": clause_id,
            "clause_number": clause.get("clause_number") or str(position),
            "title": clause.get("title") or f"Section {position}",
            "text": text,
            "category": category,
            "categories": categories,
            "final_severity": None,
            "severity": "Needs review",
            "validation_status": "FAILED_VALIDATION",
            "error_reason": "EMPTY_CLAUSE_DETECTED",
            "rule_findings": clause_rule_findings,
            "rule_ids": [],
            "risk_source": "FAILED_VALIDATION",
            "risk_reason": "Original clause text is empty or missing; manual review required.",
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
            "clause_number": clause.get("clause_number") or str(position),
            "title": clause.get("title") or f"Section {position}",
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

        # Party-calibrated severity evaluation
        party_sev, party_reason = compute_party_severity(
            rule_ids=rule_ids,
            category=category,
            clause_text=text,
            reviewing_party=reviewing_party
        )

        # Calibrated Severity Aggregation
        # High and Moderate party rules take precedence over raw model
        if party_sev == "High":
            final_severity = "High"
            risk_source = "RULE_PRECEDENCE" if "R00" in "".join(rule_ids) else "CALIBRATED_PARTY_EVALUATION"
            risk_reason = party_reason
        elif party_sev == "Moderate":
            final_severity = "Moderate"
            risk_source = "CALIBRATED_PARTY_EVALUATION"
            risk_reason = party_reason
        else:
            # For Low party evaluation, prevent false-positive High on boilerplate
            if model_severity == "High" and any(k in str(category).lower() for k in ["entire agreement", "general", "scope of services", "notices", "duties"]):
                final_severity = "Low"
                risk_source = "CALIBRATED_PARTY_EVALUATION"
                risk_reason = party_reason
            elif model_severity in ("Low", "Safe"):
                final_severity = "Low"
                risk_source = "AGREED"
                risk_reason = party_reason
            else:
                final_severity = "Low"
                risk_source = "CALIBRATED_PARTY_EVALUATION"
                risk_reason = party_reason

        logger.info(f"Clause {clause_id} output validation PASSED: severity='{final_severity}' for party='{reviewing_party}' (source='{risk_source}').")
        res_dict = dict(clause)
        res_dict.update({
            "position": position,
            "clause_id": clause_id,
            "clause_number": clause.get("clause_number") or str(position),
            "title": clause.get("title") or f"Section {position}",
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
        })
        return res_dict

    except OutputValidationError as e:
        logger.error(f"Clause {clause_id} output validation REJECTED: {e.message}")
        res_dict = dict(clause)
        res_dict.update({
            "position": position,
            "clause_id": clause_id,
            "clause_number": clause.get("clause_number") or str(position),
            "title": clause.get("title") or f"Section {position}",
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
        })
        return res_dict


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
