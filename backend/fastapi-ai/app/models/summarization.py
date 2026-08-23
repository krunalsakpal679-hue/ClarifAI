"""
ClarifAI BART Summarization Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
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
