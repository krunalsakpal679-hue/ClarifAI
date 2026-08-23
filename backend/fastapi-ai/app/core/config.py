"""
ClarifAI FastAPI Core Configuration Module
Loads environment-driven settings using pydantic-settings.
"""

import os
from typing import Optional
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

    # Local AI Model Checkpoint Identifiers
    LEGAL_BERT_MODEL_NAME: str = "nlpaueb/legal-bert-base-uncased"
    EMBEDDING_MODEL_NAME: str = "intfloat/multilingual-e5-base"
    BART_MODEL_NAME: str = "facebook/bart-base"
    TESSERACT_CMD: Optional[str] = None

    # Versioning Tags
    SCHEMA_VERSION: str = "1.0.0"
    PROMPT_VERSION: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
