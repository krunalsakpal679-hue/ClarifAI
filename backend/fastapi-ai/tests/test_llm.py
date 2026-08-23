"""
Groq LLM Client Unit Tests
"""

import os
import pytest
from app.services.llm_client import (
    get_groq_api_key,
    get_groq_model_name,
    get_llm_timeout,
    sanitize_error_message,
    get_llm_status
)


def test_groq_model_name():
    model_name = get_groq_model_name()
    assert "gpt-oss" in model_name.lower() or "openai" in model_name.lower() or "llama" in model_name.lower()


def test_llm_timeout_default():
    timeout = get_llm_timeout()
    assert isinstance(timeout, int)
    assert timeout > 0


def test_sanitize_error_message_redacts_api_key():
    fake_key = "gsk_test123456789secretkey"
    os.environ["GROQ_API_KEY"] = fake_key
    
    raw_error = f"APIError: Failed with key {fake_key} on model openai/gpt-oss-20b"
    sanitized = sanitize_error_message(raw_error)
    
    assert fake_key not in sanitized
    assert "gsk_***[REDACTED]***" in sanitized


def test_get_llm_status():
    status = get_llm_status()
    assert "configured" in status
    assert "model_name" in status
