"""
ClarifAI Groq Health & Diagnostics Unit Tests (AI-PHASE-LLM-HEALTH)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.llm_client import get_groq_api_key, get_groq_model_name, get_llm_status

client = TestClient(app)


def test_groq_model_name_default_and_env():
    """Verifies that the Groq model name is read from GROQ_MODEL_NAME."""
    model_name = get_groq_model_name()
    assert model_name == settings.GROQ_MODEL_NAME
    assert model_name == "openai/gpt-oss-20b"


def test_health_llm_endpoint_redaction_and_mode():
    """Verifies GET /health/llm returns redacted key and active mode without leaking raw secret."""
    response = client.get("/health/llm")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "mode" in data
    assert data["mode"] in ["LLM mode", "Limited mode (LLM unavailable)"]
    assert "model_name" in data
    assert data["model_name"] == "openai/gpt-oss-20b"

    # Ensure raw API key is never exposed
    if data.get("key_redacted"):
        assert "gsk_" in data["key_redacted"]
        assert "[REDACTED]" in data["key_redacted"]
        raw_key = get_groq_api_key()
        if raw_key:
            assert raw_key != data["key_redacted"]
