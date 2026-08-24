"""
ClarifAI Multilingual Embedding Schemas (AI-PHASE-EMBEDDINGS)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.common import SCHEMA_VERSION


class EmbeddingClauseItem(BaseModel):
    clause_id: Optional[str] = Field(None, description="Unique clause ID string")
    position: Optional[int] = Field(None, description="Clause index position")
    text: str = Field(..., description="Clause text to embed")
    original_text: Optional[str] = Field(None, description="Original uncleaned clause text for source fidelity")


class EmbeddingRequest(BaseModel):
    clauses: List[Dict[str, Any]] = Field(..., description="List of document clause dict items to embed")


class SingleEmbeddingRequest(BaseModel):
    text: str = Field(..., description="Clause text or user query text")
    is_query: bool = Field(False, description="True if embedding a user query (prefix 'query: '), False for passage (prefix 'passage: ')")


class SingleEmbeddingResponse(BaseModel):
    embedding: List[float] = Field(..., description="Dense 768-dimensional vector embedding")
    dimension: int = Field(768, description="Vector dimension size")
    model_name: str = Field(..., description="Multilingual-E5 model checkpoint string")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")


class EmbeddingResponse(BaseModel):
    success: bool = Field(True, description="True if embedding pipeline completed successfully")
    model_name: str = Field(..., description="Loaded embedding model checkpoint string")
    vector_dimension: int = Field(768, description="Actual output vector dimension from model")
    total_clauses: int = Field(..., description="Total clauses processed")
    embedded_clauses: List[Dict[str, Any]] = Field(..., description="Clauses augmented with 768-dim embeddings")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
