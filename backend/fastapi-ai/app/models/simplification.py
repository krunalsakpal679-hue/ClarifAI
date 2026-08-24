"""
ClarifAI Plain-Language Clause Simplification Schemas (AI-PHASE-SIMPLIFICATION)
Defines Pydantic models for per-clause plain-language simplification and why-flagged explanations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.common import SCHEMA_VERSION


class SimplificationResult(BaseModel):
    position: int = Field(..., description="1-indexed clause position")
    clause_id: Optional[str] = Field(None, description="Clause ID or position index")
    original_text: str = Field(..., description="Verbatim original clause text")
    simplified_text: str = Field(..., description="Plain language simplified rewrite")
    why_flagged: Optional[str] = Field(None, description="Grounded explanation of why the clause was flagged")
    severity: str = Field("Safe", description="Clause risk severity: High, Moderate, Low, or Safe")
    status: str = Field("SUCCESS", description="Simplification status tag: SUCCESS or FAILED_SIMPLIFICATION")


class SimplificationLLMOutput(BaseModel):
    simplified_text: str = Field(..., description="Plain-language rewrite of the clause")
    why_flagged: str = Field(..., description="Explanation of risk signal or 'No risk signals flagged for this clause.'")


class SimplificationRequest(BaseModel):
    clauses: List[Dict[str, Any]] = Field(..., description="List of clause dict items (text, severity, position, categories)")
    rule_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Optional Stage 1 rule engine findings")


class SimplificationResponse(BaseModel):
    success: bool = Field(True, description="True on simplification completion")
    total_clauses: int = Field(..., description="Total count of processed clauses")
    clauses: List[SimplificationResult] = Field(..., description="List of simplified clause items")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
