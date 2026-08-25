"""
ClarifAI Common Pydantic Response Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List

SCHEMA_VERSION: str = "1.0.0"


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error explanation")
    details: Optional[Any] = Field(None, description="Additional context or validation errors")


class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Always False for error responses")
    error: ErrorDetail
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
