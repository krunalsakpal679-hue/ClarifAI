"""
ClarifAI FastAPI Core Configuration Module
Loads environment-driven settings using pydantic-settings.
"""

import os
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "ClarifAI AI Microservice"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Network & Internal Security
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    INTERNAL_SERVICE_SECRET: Optional[str] = None

    # Groq LLM Cloud Service Settings
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL_NAME: str = "openai/gpt-oss-20b"
    LLM_REQUEST_TIMEOUT_SECONDS: int = 30

    # Qdrant Vector Database Settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "clarifai_clause_embeddings"

    # RAG Gating Threshold Settings (Configurable, Internal Only)
    RAG_RELEVANCE_THRESHOLD: float = 0.65
    RAG_SUFFICIENCY_THRESHOLD: float = 0.70

    # Pairwise Comparison Threshold Settings
    COMPARISON_MATCHED_THRESHOLD: float = 0.88
    COMPARISON_CHANGED_THRESHOLD: float = 0.65

    # Local AI Model Checkpoint Identifiers (Fine-Tuned Validated Checkpoints)
    LEGAL_BERT_MODEL_NAME: str = "backend/fastapi-ai/training/checkpoints/legal-bert/v2.0"
    EMBEDDING_MODEL_NAME: str = "backend/fastapi-ai/training/checkpoints/multilingual-e5/v1.1"
    BART_MODEL_NAME: str = "facebook/bart-base"
    TESSERACT_CMD: Optional[str] = None

    # Versioning Tags
    SCHEMA_VERSION: str = "1.0.0"
    PROMPT_VERSION: str = "1.0.0"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        is_dev = self.ENVIRONMENT.lower() in ["development", "dev", "test", "testing", "local"]
        if not is_dev and not self.INTERNAL_SERVICE_SECRET:
            raise ValueError(
                "INTERNAL_SERVICE_SECRET environment variable must be set in production."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
