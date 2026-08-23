"""
ClarifAI Risk Classification Schemas
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
    confidence: float = Field(..., description="Softmax confidence score (0.0 to 1.0)")
    logits_shape: List[int] = Field(..., description="Shape of output tensor logits")
    latency_ms: float = Field(..., description="Inference execution latency in milliseconds")
    is_interim_placeholder: bool = Field(True, description="Indicates base model interim status")
    model_name: str = Field(..., description="Loaded Legal-BERT checkpoint string")
    rule_findings_included: bool = Field(..., description="Whether Stage 1 rule signals were provided")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
