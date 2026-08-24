"""
ClarifAI BART Summarization Schemas (AI-PHASE-SUMMARY)
Defines single-section and 4-field document-level executive summarization schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.common import SCHEMA_VERSION


class SummarizationRequest(BaseModel):
    text: str = Field(..., description="Document or section text to summarize")
    max_length: Optional[int] = Field(200, description="Maximum summary token length")
    min_length: Optional[int] = Field(30, description="Minimum summary token length")


class SummarizationResponse(BaseModel):
    summary: str = Field(..., description="Generated summary text")
    token_count: int = Field(..., description="Summary token count")
    max_length_setting: int = Field(..., description="Configured maximum length")
    min_length_setting: int = Field(..., description="Configured minimum length")
    latency_ms: float = Field(..., description="Generation execution latency in milliseconds")
    is_chunked: bool = Field(..., description="Whether input text exceeded 1024 tokens and required chunking")
    num_chunks_processed: int = Field(..., description="Number of text chunks processed")
    model_name: str = Field(..., description="Loaded BART checkpoint model string")
    is_interim_placeholder: bool = Field(True, description="Indicates base model interim status")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")


class DocumentSummaryRequest(BaseModel):
    clauses: List[Dict[str, Any]] = Field(..., description="List of document clause dict items")
    rule_findings: Optional[List[Dict[str, Any]]] = Field(None, description="Optional Stage 1 rule engine findings")


class DocumentSummaryResponse(BaseModel):
    success: bool = Field(True, description="True if document summary generation succeeded")
    summary_status: str = Field("AVAILABLE", description="Status tag: AVAILABLE or UNAVAILABLE")
    purpose_text: Optional[str] = Field(None, description="Executive summary of document purpose")
    obligations_text: Optional[str] = Field(None, description="Executive summary of primary obligations")
    key_terms_text: Optional[str] = Field(None, description="Executive summary of key terms & provisions")
    key_risks_text: Optional[str] = Field(None, description="Executive roll-up summary of flagged legal risks")
    summary_error: Optional[str] = Field(None, description="Error reason if summary is UNAVAILABLE")
    latency_ms: Optional[float] = Field(None, description="Total summarization execution latency in ms")
    model_name: str = Field(..., description="BART model checkpoint string")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
