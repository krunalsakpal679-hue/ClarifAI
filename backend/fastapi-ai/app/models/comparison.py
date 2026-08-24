"""
Pydantic Data Models for Pairwise Document Comparison Service (AI-PHASE-COMPARISON)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.common import SCHEMA_VERSION


class ComparisonRequest(BaseModel):
    user_id: str = Field(..., description="Owner user ID string for defensive ownership validation")
    document_id_a: str = Field(..., description="Baseline document ID (Document A)")
    document_id_b: str = Field(..., description="Revised document ID (Document B)")
    matched_threshold: Optional[float] = Field(default=0.88, description="Similarity threshold for MATCHED classification")
    changed_threshold: Optional[float] = Field(default=0.65, description="Similarity threshold for CHANGED classification")


class ClauseComparisonItem(BaseModel):
    clause_id_a: Optional[str] = Field(None, description="Clause ID from Document A")
    clause_id_b: Optional[str] = Field(None, description="Clause ID from Document B")
    position_a: Optional[int] = Field(None, description="Clause position in Document A")
    position_b: Optional[int] = Field(None, description="Clause position in Document B")
    text_a: Optional[str] = Field(None, description="Text of Clause A")
    text_b: Optional[str] = Field(None, description="Text of Clause B")
    similarity_score: float = Field(..., description="Cosine similarity score between vectors")
    classification: str = Field(..., description="Classification label: MATCHED, CHANGED, or MISSING")
    difference_explanation: Optional[str] = Field(None, description="Grounded LLM difference explanation for CHANGED pairs")


class ComparisonResponse(BaseModel):
    success: bool = Field(True, description="Execution status boolean")
    user_id: str = Field(..., description="Owner user ID")
    document_id_a: str = Field(..., description="Baseline document ID")
    document_id_b: str = Field(..., description="Revised document ID")
    total_clauses_a: int = Field(..., description="Clause count in Document A")
    total_clauses_b: int = Field(..., description="Clause count in Document B")
    matched_count: int = Field(..., description="Number of MATCHED clause pairs")
    changed_count: int = Field(..., description="Number of CHANGED clause pairs")
    missing_count: int = Field(..., description="Number of MISSING/ADDED clause pairs")
    is_low_confidence: bool = Field(False, description="Flag indicating documents have significantly different structure/length")
    confidence_warning: Optional[str] = Field(None, description="Detailed warning message if low confidence")
    comparison_results: List[ClauseComparisonItem] = Field(..., description="Pairwise comparison classification items")
    schema_version: str = Field(SCHEMA_VERSION, description="Schema version identifier")
