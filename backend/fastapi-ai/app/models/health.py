"""
ClarifAI Health Pydantic Response Schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.models.common import SCHEMA_VERSION


class ComponentHealth(BaseModel):
    status: str = Field(..., description="Operational status: healthy, degraded, or error")
    details: Optional[Dict[str, Any]] = Field(None, description="Component-specific diagnostics")


class HealthStatusResponse(BaseModel):
    status: str = Field(..., description="Overall service status: ok, healthy, or degraded")
    service: str = Field("fastapi-ai", description="Microservice identifier")
    version: str = Field("0.1.0", description="Microservice build version")
    environment: str = Field("development", description="Runtime environment")
    groq_configured: bool = Field(..., description="Whether Groq API key is present")
    qdrant_configured: bool = Field(..., description="Whether Qdrant URL is present")
    tesseract: Optional[Dict[str, Any]] = None
    embedding: Optional[Dict[str, Any]] = None
    legal_bert: Optional[Dict[str, Any]] = None
    llm: Optional[Dict[str, Any]] = None
    summarization: Optional[Dict[str, Any]] = None
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
