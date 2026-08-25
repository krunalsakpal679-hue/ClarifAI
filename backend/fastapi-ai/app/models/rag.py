"""
ClarifAI RAG Pipeline Schemas (AI-PHASE-RAG)
Defines request and response models for RAG evidence retrieval and two-stage gating evaluation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.common import SCHEMA_VERSION


class RAGRequest(BaseModel):
    user_id: str = Field(..., description="Owner user ID string (MANDATORY)")
    document_id: str = Field(..., description="Target document ID string (MANDATORY)")
    question: str = Field(..., description="User query question string")
    top_k: Optional[int] = Field(5, description="Candidate retrieval limit")
    relevance_threshold: Optional[float] = Field(None, description="Optional override for Stage 1 relevance threshold")
    sufficiency_threshold: Optional[float] = Field(None, description="Optional override for Stage 2 sufficiency threshold")


class RAGEvidenceItem(BaseModel):
    clause_id: str = Field(..., description="Evidence clause ID")
    position: int = Field(..., description="Clause sequence position")
    text: str = Field(..., description="Clause text string")
    original_text: str = Field(..., description="Original uncleaned clause text")
    severity: str = Field("Safe", description="Clause risk severity label")
    categories: List[str] = Field(default_factory=list, description="Assigned category labels")
    score: float = Field(..., description="Cosine similarity relevance score")


class RAGEvaluationResponse(BaseModel):
    has_sufficient_evidence: bool = Field(..., description="True if both Stage 1 and Stage 2 gates passed")
    relevance_gate_passed: bool = Field(..., description="True if Stage 1 Relevance Gate passed")
    sufficiency_gate_passed: bool = Field(..., description="True if Stage 2 Sufficiency Gate passed")
    no_answer_reason: Optional[str] = Field(None, description="Controlled no-answer reason if gating failed")
    validated_evidence: List[RAGEvidenceItem] = Field(default_factory=list, description="Validated evidence clauses for LLM generation")
    user_id: str = Field(..., description="Verified owner user ID filter")
    document_id: str = Field(..., description="Verified document ID filter")
    question: str = Field(..., description="Evaluated question string")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
