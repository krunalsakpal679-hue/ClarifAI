"""
ClarifAI Clause Segmentation Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.common import SCHEMA_VERSION


class ClauseItem(BaseModel):
    position: int = Field(..., description="1-indexed sequential clause position")
    clause_number: Optional[str] = Field(None, description="Extracted source clause number (e.g. Section 1.1, Clause 4, 1.2)")
    title: Optional[str] = Field(None, description="Extracted clause heading/title if present")
    text: str = Field(..., description="Verbatim original clause text (unmodified)")
    character_count: int = Field(..., description="Total non-whitespace character count of clause text")
    page_number: Optional[int] = Field(None, description="Associated source page number for evidence traceability")


class ClauseSegmentationRequest(BaseModel):
    text: str = Field(..., description="Cleaned document text to segment into legal clauses")
    document_id: Optional[str] = Field(None, description="Optional document tracking identifier")
    pages: Optional[List[dict]] = Field(None, description="Optional per-page text list for page reference mapping")


class ClauseSegmentationResponse(BaseModel):
    success: bool = Field(True, description="True on successful clause segmentation")
    total_clauses: int = Field(..., description="Total count of segmented clauses")
    clauses: List[ClauseItem] = Field(..., description="Ordered list of segmented clause records")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
