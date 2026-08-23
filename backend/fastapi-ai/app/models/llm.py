"""
ClarifAI Groq LLM Completion Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.common import SCHEMA_VERSION


class LLMCompletionRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or structured instruction")
    system_prompt: Optional[str] = Field("You are a legal contract AI assistant.", description="System context role prompt")
    temperature: Optional[float] = Field(0.1, description="Sampling temperature")
    max_tokens: Optional[int] = Field(500, description="Maximum completion tokens")


class LLMCompletionResponse(BaseModel):
    success: bool = Field(True, description="True on successful completion")
    content: str = Field(..., description="Generated text completion")
    model_name: str = Field(..., description="Active Groq model name identifier")
    latency_ms: float = Field(..., description="API round-trip latency in milliseconds")
    usage: Dict[str, Any] = Field(default_factory=dict, description="Token usage statistics")
    attempt: int = Field(1, description="Attempt count (1 if first try)")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
    prompt_version: str = Field("1.0.0", description="System prompt version tag")
