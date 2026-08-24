"""
ClarifAI Chatbot Schemas (AI-PHASE-CHATBOT)
Defines request and response models for contract-grounded RAG chatbot conversation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.common import SCHEMA_VERSION


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role ('user' or 'assistant')")
    content: str = Field(..., description="Message text content")


class ChatbotRequest(BaseModel):
    session_id: str = Field(..., description="Unique chat session ID string (MANDATORY)")
    user_id: str = Field(..., description="Owner user ID string (MANDATORY)")
    document_id: str = Field(..., description="Target document ID string (MANDATORY)")
    question: str = Field(..., description="User query question string")
    top_k: Optional[int] = Field(5, description="Candidate clause retrieval limit")


class ChatbotResponse(BaseModel):
    answer: str = Field(..., description="Grounded answer text or controlled no-answer response")
    has_sufficient_evidence: bool = Field(..., description="True if evidence gate passed")
    source_clause_ids: List[str] = Field(default_factory=list, description="Traceable evidence clause IDs")
    disclaimer: str = Field(..., description="Standard non-legal advice disclaimer")
    session_id: str = Field(..., description="Verified session ID")
    user_id: str = Field(..., description="Verified owner user ID")
    document_id: str = Field(..., description="Verified target document ID")
    question: str = Field(..., description="Evaluated question string")
    schema_version: str = Field(SCHEMA_VERSION, description="Semver schema version tag")
