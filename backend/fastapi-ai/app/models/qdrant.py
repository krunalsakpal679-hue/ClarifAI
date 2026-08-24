"""
ClarifAI Qdrant Vector Database Integration Schemas (AI-PHASE-QDRANT)
Defines request and response models for document indexing, scoped query, and deletion.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.common import SCHEMA_VERSION


class QdrantIndexRequest(BaseModel):
    user_id: str = Field(..., description="Owner user ID string (MANDATORY)")
    document_id: str = Field(..., description="Target document ID string (MANDATORY)")
    clauses: List[Dict[str, Any]] = Field(..., description="List of classified and simplified clause items")


class QdrantIndexResponse(BaseModel):
    success: bool = Field(True, description="True if document indexing completed successfully")
    indexed_points: int = Field(..., description="Number of vector points upserted to Qdrant")
    document_id: str = Field(..., description="Indexed document ID")
    user_id: str = Field(..., description="Owner user ID")
    collection_name: str = Field(..., description="Qdrant collection name")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")


class QdrantQueryRequest(BaseModel):
    user_id: str = Field(..., description="Owner user ID string (MANDATORY for hard filtering)")
    document_id: str = Field(..., description="Target document ID string (MANDATORY for hard filtering)")
    query_text: Optional[str] = Field(None, description="Optional search query string (auto-embedded using Multilingual-E5 query prefix)")
    query_vector: Optional[List[float]] = Field(None, description="Optional raw 768-dimensional float list query vector")
    top_k: Optional[int] = Field(5, description="Maximum matches to retrieve")


class QdrantQueryResultItem(BaseModel):
    clause_id: str = Field(..., description="Matching clause ID")
    document_id: str = Field(..., description="Document ID")
    user_id: str = Field(..., description="Owner user ID")
    position: int = Field(..., description="Clause sequence position")
    language: str = Field("en", description="Clause language tag")
    text: str = Field(..., description="Clause text")
    original_text: str = Field(..., description="Original uncleaned clause text")
    severity: str = Field(..., description="Classifier severity level")
    categories: List[str] = Field(default_factory=list, description="Assigned category labels")
    simplified_text: Optional[str] = Field(None, description="Plain-language simplification text")
    why_flagged: Optional[str] = Field(None, description="Why flagged explanation text")
    score: float = Field(..., description="Cosine similarity score")


class QdrantQueryResponse(BaseModel):
    success: bool = Field(True, description="True if scoped query executed successfully")
    results: List[Dict[str, Any]] = Field(..., description="Matching clause items with similarity score")
    total_matches: int = Field(..., description="Number of matching clauses returned")
    user_id: str = Field(..., description="Verified owner user ID filter")
    document_id: str = Field(..., description="Verified document ID filter")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")


class QdrantDeleteRequest(BaseModel):
    user_id: str = Field(..., description="Owner user ID string (MANDATORY)")
    document_id: str = Field(..., description="Target document ID string (MANDATORY)")


class QdrantDeleteResponse(BaseModel):
    success: bool = Field(True, description="True if document points deletion succeeded")
    deleted_document_id: str = Field(..., description="Deleted document ID")
    user_id: str = Field(..., description="Owner user ID")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
