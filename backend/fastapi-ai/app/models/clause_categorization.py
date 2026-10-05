"""
ClarifAI Legal Clause Categorization Pydantic Schemas & Enum
(W3 Expanded Taxonomy)
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.models.common import SCHEMA_VERSION
from app.models.clause_segmentation import ClauseItem


class ClauseCategoryEnum(str, Enum):
    # 24 Canonical Taxonomy Categories (Master Prompt Section 4.4)
    SCOPE_OF_SERVICES = "Scope of Services"
    PAYMENT = "Payment"
    TERM = "Term"
    RENEWAL = "Renewal"
    TERMINATION = "Termination"
    CONFIDENTIALITY = "Confidentiality"
    IP_WORK_PRODUCT = "IP/Work Product"
    INDEMNIFICATION = "Indemnification"
    LIMITATION_OF_LIABILITY = "Limitation of Liability"
    INSURANCE = "Insurance"
    PRIVACY = "Privacy"
    DISPUTE_RESOLUTION = "Dispute Resolution"
    GOVERNING_LAW = "Governing Law"
    RESTRICTIVE_COVENANTS = "Restrictive Covenants"
    PREMISES = "Premises"
    USE = "Use"
    MAINTENANCE = "Maintenance"
    ALTERATIONS = "Alterations"
    COMPLIANCE_LEGAL = "Compliance/Legal"
    AUDIT_AND_RECORDS = "Audit and Records"
    SUBCONTRACTING = "Subcontracting"
    ASSIGNMENT = "Assignment"
    NOTICES = "Notices"
    ENTIRE_AGREEMENT_GENERAL = "Entire Agreement/General"

    # Backward-compatible Taxonomy Aliases (Mapped to Canonical 24 Values)
    INTELLECTUAL_PROPERTY = "IP/Work Product"
    PROPERTY_PREMISES = "Premises"
    PROPERTY_USE = "Use"
    WARRANTY = "Warranty"
    FORCE_MAJEURE = "Force Majeure"
    GENERAL_BOILERPLATE = "Entire Agreement/General"
    GENERAL = "Entire Agreement/General"
    LIABILITY = "Limitation of Liability"
    AUDIT_INSPECTION = "Audit and Records"


APPROVED_CATEGORIES_SET = {category.value for category in ClauseCategoryEnum} | {
    "Intellectual Property",
    "Property / Premises",
    "Property Use",
    "General / Boilerplate",
    "General",
    "Liability",
    "Audit / Inspection",
    "Force Majeure",
    "Warranty",
}


class CategorizedClauseItem(ClauseItem):
    categories: List[ClauseCategoryEnum] = Field(
        default_factory=list,
        description="List of validated categories from the approved taxonomy"
    )

    @field_validator("categories")
    @classmethod
    def validate_categories_in_set(cls, categories: List[ClauseCategoryEnum]) -> List[ClauseCategoryEnum]:
        for cat in categories:
            val = cat.value if isinstance(cat, ClauseCategoryEnum) else str(cat)
            if val not in APPROVED_CATEGORIES_SET:
                raise ValueError(f"Category '{val}' is outside the approved category set.")
        return categories


class ClauseCategorizationRequest(BaseModel):
    clauses: List[ClauseItem] = Field(..., description="List of segmented clause items to categorize")
    rule_findings: Optional[List[dict]] = Field(None, description="Optional rule engine findings for category signal weighting")


class ClauseCategorizationResponse(BaseModel):
    success: bool = Field(True, description="True on successful clause categorization")
    total_clauses: int = Field(..., description="Total count of categorized clauses")
    clauses: List[CategorizedClauseItem] = Field(..., description="Ordered list of categorized clause records")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
