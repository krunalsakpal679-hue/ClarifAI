"""
ClarifAI Risk Classification Schemas
Implements strict 4-level severity schemas (High, Moderate, Low, Safe)
with per-clause risk payload omitting numeric confidence scores per Chapter 16.9.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.common import SCHEMA_VERSION


class ClauseRiskRequest(BaseModel):
    clause_text: str = Field(..., description="Target contract clause text to classify")
    rule_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Optional Stage 1 rule engine signals")


class ClauseRiskResponse(BaseModel):
    success: bool = Field(True, description="True on successful classification")
    severity: str = Field(..., description="Strict 4-level severity: High, Moderate, Low, Safe")
    confidence: float = Field(..., description="Internal Softmax confidence score (0.0 to 1.0)")
    logits_shape: List[int] = Field(..., description="Shape of output tensor logits")
    latency_ms: float = Field(..., description="Inference execution latency in milliseconds")
    is_interim_placeholder: bool = Field(True, description="Indicates base model interim status")
    model_name: str = Field(..., description="Loaded Legal-BERT checkpoint string")
    rule_findings_included: bool = Field(..., description="Whether Stage 1 rule signals were provided")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")


class ClassifiedClauseItem(BaseModel):
    position: int = Field(..., description="1-indexed clause position")
    clause_id: Optional[str] = Field(None, description="Clause ID or position index")
    text: str = Field(..., description="Verbatim clause text")
    severity: Optional[str] = Field(None, description="Strict severity label: High, Moderate, Low, or Safe")
    final_severity: Optional[str] = Field(None, description="Validated final severity label")
    validation_status: str = Field("VALIDATED", description="Status tag: VALIDATED or FAILED_VALIDATION")
    error_reason: Optional[str] = Field(None, description="Error reason if validation failed")
    rule_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Associated Stage 1 rule findings preserved unaltered")


class DocumentRiskRequest(BaseModel):
    clauses: List[Dict[str, Any]] = Field(..., description="List of clause dict items to classify")
    rule_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Optional Stage 1 rule engine findings")


class DocumentRiskResponse(BaseModel):
    success: bool = Field(True, description="True on successful multi-clause risk classification")
    total_clauses: int = Field(..., description="Total count of processed clauses")
    clauses: List[ClassifiedClauseItem] = Field(..., description="List of classified clause items with per-clause isolation")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")


class OutputValidationRequest(BaseModel):
    clause: Dict[str, Any] = Field(..., description="Target clause dict")
    raw_classification: Optional[Dict[str, Any]] = Field(None, description="Raw output dict from classifier")
    rule_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Optional Stage 1 rule findings")


class OutputValidationResponse(BaseModel):
    success: bool = Field(True, description="True on output validation completion")
    result: ClassifiedClauseItem = Field(..., description="Validated clause risk item")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
