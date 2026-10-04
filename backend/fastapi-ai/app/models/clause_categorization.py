"""
ClarifAI Legal Clause Categorization Pydantic Schemas & Enum
Enforces the fixed, PRD-approved 8-category set per Chapter 56.9.
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from app.models.common import SCHEMA_VERSION
from app.models.clause_segmentation import ClauseItem


class ClauseCategoryEnum(str, Enum):
    SCOPE_OF_SERVICES = "Scope of Services"
    PAYMENT = "Payment"
    CONFIDENTIALITY = "Confidentiality"
    INTELLECTUAL_PROPERTY = "Intellectual Property"
    INDEMNIFICATION = "Indemnification"
    LIMITATION_OF_LIABILITY = "Limitation of Liability"
    TERM = "Term"
    TERMINATION = "Termination"
    RENEWAL = "Renewal"
    DISPUTE_RESOLUTION = "Dispute Resolution"
    GOVERNING_LAW = "Governing Law"
    RESTRICTIVE_COVENANTS = "Restrictive Covenants"
    PROPERTY_PREMISES = "Property / Premises"
    PROPERTY_USE = "Property Use"
    MAINTENANCE = "Maintenance"
    ALTERATIONS = "Alterations"
    GENERAL_BOILERPLATE = "General / Boilerplate"
    PRIVACY = "Privacy"
    LIABILITY = "Limitation of Liability"


APPROVED_CATEGORIES_SET = {category.value for category in ClauseCategoryEnum}


class CategorizedClauseItem(ClauseItem):
    categories: List[ClauseCategoryEnum] = Field(
        default_factory=list,
        description="List of validated categories from the fixed 8-value PRD set"
    )

    @field_validator("categories")
    @classmethod
    def validate_categories_in_set(cls, categories: List[ClauseCategoryEnum]) -> List[ClauseCategoryEnum]:
        for cat in categories:
            val = cat.value if isinstance(cat, ClauseCategoryEnum) else str(cat)
            if val not in APPROVED_CATEGORIES_SET:
                raise ValueError(f"Category '{val}' is outside the fixed PRD-approved 8-category set.")
        return categories


class ClauseCategorizationRequest(BaseModel):
    clauses: List[ClauseItem] = Field(..., description="List of segmented clause items to categorize")
    rule_findings: Optional[List[dict]] = Field(None, description="Optional rule engine findings for category signal weighting")


class ClauseCategorizationResponse(BaseModel):
    success: bool = Field(True, description="True on successful clause categorization")
    total_clauses: int = Field(..., description="Total count of categorized clauses")
    clauses: List[CategorizedClauseItem] = Field(..., description="Ordered list of categorized clause records")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
