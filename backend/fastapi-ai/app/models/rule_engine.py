"""
ClarifAI Rule Engine Pydantic Schemas
Strictly excludes severity/risk_level fields per Chapter 16.10.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.common import SCHEMA_VERSION

RULE_SET_VERSION: str = "v1.0"


class RuleFinding(BaseModel):
    rule_id: str = Field(..., description="Rule identifier (e.g. R001, R002, ..., R014)")
    risk_signal: str = Field(..., description="Human-readable risk signal title")
    matched_text: str = Field(..., description="Exact matched text snippet")
    clause_id: Optional[str] = Field(None, description="Clause ID or position index associated with match")
    evidence: str = Field(..., description="Contextual evidence span surrounding match")
    rule_version: str = Field(RULE_SET_VERSION, description="Rule set semver tag (v1.0)")
    match_status: str = Field("MATCH", description="Status of rule match")


class RuleEngineRequest(BaseModel):
    clauses: Optional[List[dict]] = Field(None, description="List of clause dict objects from clause processing stage")
    text: Optional[str] = Field(None, description="Raw or cleaned document text string")


class RuleEngineResponse(BaseModel):
    success: bool = Field(True, description="True on successful rule evaluation")
    total_findings: int = Field(..., description="Total count of matched rule findings")
    findings: List[RuleFinding] = Field(..., description="List of rule finding records")
    rule_set_version: str = Field(RULE_SET_VERSION, description="Rule set version tag (v1.0)")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
