"""
ClarifAI Legal Text Cleaning Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import List
from app.models.common import SCHEMA_VERSION


class TextCleaningRequest(BaseModel):
    raw_text: str = Field(..., description="Raw text extracted from PDF or OCR to clean and normalize")
    preserve_page_markers: bool = Field(True, description="Whether to preserve [PAGE:X] structural markers")


class TextCleaningResponse(BaseModel):
    success: bool = Field(True, description="True on successful cleaning")
    cleaned_text: str = Field(..., description="Cleaned and normalized legal text")
    original_length: int = Field(..., description="Original raw text character count")
    cleaned_length: int = Field(..., description="Cleaned text character count")
    rules_applied: List[str] = Field(..., description="List of deterministic cleaning rules executed")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
