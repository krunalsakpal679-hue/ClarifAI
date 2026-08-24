"""
Pydantic Schemas for Multilingual English-to-Hindi Translation Service (AI-PHASE-MULTILINGUAL)
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.models.common import SCHEMA_VERSION


class TranslationRequest(BaseModel):
    user_id: str = Field(..., description="Owner user ID string (MANDATORY)")
    document_id: str = Field(..., description="Target document ID string (MANDATORY)")
    summary: Dict[str, Any] = Field(..., description="English document summary dict")
    clauses: List[Dict[str, Any]] = Field(..., description="List of English clause dicts")
    target_language: Optional[str] = Field("hi", description="Target language ('hi' for Hindi)")


class TranslationResponse(BaseModel):
    success: bool = Field(True, description="Execution status boolean")
    user_id: str = Field(..., description="Verified owner user ID")
    document_id: str = Field(..., description="Verified target document ID")
    target_language: str = Field("hi", description="Target language code")
    summary_hi: Dict[str, Any] = Field(..., description="Translated summary fields or English fallback")
    clauses_hi: List[Dict[str, Any]] = Field(..., description="Translated clause list with original_text intact")
    translation_status: str = Field(..., description="'SUCCESS' or 'TRANSLATION_UNAVAILABLE'")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
