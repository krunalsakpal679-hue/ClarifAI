"""
ClarifAI Legal Clause Categorization Service Module
Implements clause categorization into the fixed PRD-approved 8-category set,
with structured output validation rejecting any out-of-set values per Chapter 56.9.
"""

import re
import logging
from typing import Dict, Any, List
from fastapi import HTTPException, status
from app.models.clause_categorization import ClauseCategoryEnum, APPROVED_CATEGORIES_SET

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"

# Keyword & regex match patterns for each of the 8 approved categories
CATEGORY_PATTERNS = {
    ClauseCategoryEnum.PAYMENT: re.compile(
        r"\b(?:payment|pay|fee|fees|invoice|remit|billing|charge|costs?|price|currency|compensation|\$|₹|€)\b",
        re.IGNORECASE
    ),
    ClauseCategoryEnum.TERMINATION: re.compile(
        r"\b(?:terminate|termination|expire|expiration|cancel|cancellation|breach|default|wind\s*down)\b",
        re.IGNORECASE
    ),
    ClauseCategoryEnum.RENEWAL: re.compile(
        r"\b(?:renew|renewal|extension|auto-renew|automatic\s+renewal|extend\s+term)\b",
        re.IGNORECASE
    ),
    ClauseCategoryEnum.CONFIDENTIALITY: re.compile(
        r"\b(?:confidential|confidentiality|secret|proprietary|non-disclosure|nda|disclose|privacy\s+of\s+information)\b",
        re.IGNORECASE
    ),
    ClauseCategoryEnum.LIABILITY: re.compile(
        r"\b(?:liable|liability|indemnify|indemnification|limitation\s+of\s+liability|damages|hold\s+harmless|loss|losses)\b",
        re.IGNORECASE
    ),
    ClauseCategoryEnum.INTELLECTUAL_PROPERTY: re.compile(
        r"\b(?:intellectual\s+property|ip|copyright|trademark|patent|patentable|trade\s+secret|license|ownership\s+of\s+work)\b",
        re.IGNORECASE
    ),
    ClauseCategoryEnum.PRIVACY: re.compile(
        r"\b(?:privacy|personal\s+data|pii|gdpr|data\ subject|personally\ identifiable|data\ protection|processing\ of\ data)\b",
        re.IGNORECASE
    ),
    ClauseCategoryEnum.DISPUTE_RESOLUTION: re.compile(
        r"\b(?:dispute|dispute\ resolution|arbitration|arbitrator|governing\ law|jurisdiction|court|venue|litigation)\b",
        re.IGNORECASE
    ),
}


def validate_category_value(val: str) -> ClauseCategoryEnum:
    """
    Validates that a category string strictly belongs to the fixed 8-value PRD set.
    Raises HTTPException(422) if outside the set.
    """
    if val not in APPROVED_CATEGORIES_SET:
        logger.error(f"Structured output validation failed: Rejected out-of-set category '{val}'.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_CATEGORY_REJECTED",
                "message": f"Category '{val}' is outside the fixed PRD-approved 8-category set."
            }
        )
    return ClauseCategoryEnum(val)


def categorize_clause_records(clauses_input: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categorizes an ordered list of clause records into the fixed 8-value PRD category set.

    Args:
        clauses_input: List of clause dict items from clause segmentation stage.

    Returns:
        Dict containing categorized clauses list, total_clauses, and schema_version.
    """
    if not clauses_input:
        logger.warning("Categorization received empty clause list.")
        return {
            "success": True,
            "total_clauses": 0,
            "clauses": [],
            "schema_version": SCHEMA_VERSION
        }

    categorized_records: List[Dict[str, Any]] = []

    for clause in clauses_input:
        text = clause.get("text", "")
        title = clause.get("title", "") or ""
        combined_content = f"{title} {text}"

        assigned_categories: List[ClauseCategoryEnum] = []

        for category_enum, pattern in CATEGORY_PATTERNS.items():
            if pattern.search(combined_content):
                # Validate before appending
                validated_cat = validate_category_value(category_enum.value)
                assigned_categories.append(validated_cat)

        record = dict(clause)
        record["categories"] = assigned_categories
        categorized_records.append(record)

    logger.info(f"Clause Categorization Complete: {len(categorized_records)} clauses processed.")

    return {
        "success": True,
        "total_clauses": len(categorized_records),
        "clauses": categorized_records,
        "schema_version": SCHEMA_VERSION
    }
