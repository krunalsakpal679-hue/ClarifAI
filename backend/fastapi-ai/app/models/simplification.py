"""
ClarifAI Plain-Language Clause Simplification Schemas (AI-PHASE-SIMPLIFICATION)
Defines Pydantic models for per-clause plain-language simplification,
structured evidence-backed explanations, and why-flagged rationales.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.common import SCHEMA_VERSION


class RiskExplanation(BaseModel):
    severity: Optional[str] = Field(None, description="Severity label: High, Moderate, Low, Safe, or RISK_CLASSIFICATION_UNAVAILABLE")
    reason: str = Field(..., description="Grounded explanation of why this risk was assigned")
    evidence: Optional[str] = Field(None, description="Verbatim quote/substring from source clause text justifying this risk")


class CategoryExplanation(BaseModel):
    label: Optional[str] = Field(None, description="Assigned category label from 8 approved categories")
    reason: str = Field(..., description="Grounded explanation of why this category was assigned")
    evidence: Optional[str] = Field(None, description="Verbatim quote/substring from source clause text justifying this category")


class StructuredClauseExplanation(BaseModel):
    what_this_clause_means: str = Field(..., description="Plain language explanation of clause meaning")
    risk: RiskExplanation = Field(..., description="Risk assessment with grounded source evidence")
    category: CategoryExplanation = Field(..., description="Category assignment with grounded source evidence")


class SimplificationResult(BaseModel):
    position: int = Field(..., description="1-indexed clause position")
    clause_id: Optional[str] = Field(None, description="Clause ID or position index")
    clause_number: Optional[str] = Field(None, description="Source clause number")
    title: Optional[str] = Field(None, description="Clause heading or title")
    original_text: str = Field(..., description="Verbatim original clause text")
    simplified_text: str = Field(..., description="Plain language simplified rewrite")
    why_flagged: Optional[str] = Field(None, description="Grounded explanation of why the clause was flagged")
    structured_explanation: Optional[StructuredClauseExplanation] = Field(None, description="Evidence-backed structured explanation")
    plain_language: Optional[str] = Field(None, description="Plain English summary")
    who_is_bound: Optional[str] = Field(None, description="Party bound")
    who_benefits: Optional[str] = Field(None, description="Party benefiting")
    key_details: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Extracted key facts")
    mode: Optional[str] = Field("LLM", description="Processing mode: LLM or Limited")
    severity: Optional[str] = Field(None, description="Clause risk severity: High, Moderate, Low, Safe, or RISK_CLASSIFICATION_UNAVAILABLE")
    status: str = Field("SUCCESS", description="Simplification status tag: SUCCESS or FAILED_SIMPLIFICATION")


class SimplificationLLMOutput(BaseModel):
    simplified_text: str = Field(..., description="Plain-language rewrite of the clause")
    why_flagged: str = Field(..., description="Explanation of risk signal or 'No risk signals flagged for this clause.'")


class SimplificationRequest(BaseModel):
    clauses: List[Dict[str, Any]] = Field(..., description="List of clause dict items (text, severity, position, categories)")
    rule_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Optional Stage 1 rule engine findings")
    document_header: Optional[Dict[str, Any]] = Field(None, description="Optional document header metadata")


class SimplificationResponse(BaseModel):
    success: bool = Field(True, description="True on simplification completion")
    total_clauses: int = Field(..., description="Total count of processed clauses")
    clauses: List[SimplificationResult] = Field(..., description="List of simplified clause items")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
