"""
Groq LLM Client & Consolidated LLM Layer Unit Tests (AI-PHASE-LLM-INTEGRATION)
"""

import os
import pytest
from unittest.mock import MagicMock
from groq import APIConnectionError, RateLimitError
from app.services.llm_client import (
    get_groq_api_key,
    get_groq_model_name,
    get_llm_timeout,
    sanitize_error_message,
    format_untrusted_evidence_block,
    check_for_legal_advice,
    check_for_prompt_injection_leak,
    validate_untrusted_llm_output,
    classify_llm_exception,
    generate_llm_completion,
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


def test_untrusted_evidence_framing_delimiter():
    """Verifies standardized untrusted evidence block wrapping."""
    clause_text = "Either party may terminate upon 30 days written notice."
    framed = format_untrusted_evidence_block(clause_text)
    
    assert "<<<UNTRUSTED_EVIDENCE_START>>>" in framed
    assert "<<<UNTRUSTED_EVIDENCE_END>>>" in framed
    assert clause_text in framed


def test_shared_validate_untrusted_llm_output():
    """Verifies shared output safety validator for legal advice and prompt injection markers."""
    # Valid output
    is_safe, val = validate_untrusted_llm_output("The contract notice period is 30 days.")
    assert is_safe is True
    assert val == "The contract notice period is 30 days."

    # Legal advice prohibited
    is_safe_la, _ = validate_untrusted_llm_output("I advise you to terminate immediately.")
    assert is_safe_la is False

    # Prompt injection leak prohibited
    is_safe_pi, _ = validate_untrusted_llm_output("Here is the output: <untrusted_clause_text> text")
    assert is_safe_pi is False


def test_classify_llm_exception_categories():
    """Verifies exception classification for rate limits, connection errors, and timeouts."""
    conn_err = APIConnectionError(request=MagicMock())
    diag_conn = classify_llm_exception(conn_err)
    assert diag_conn["category"] == "NETWORK_CONNECTION_FAILURE"
    assert diag_conn["is_transient"] is True

    timeout_err = Exception("Request timeout occurred after 30 seconds")
    diag_to = classify_llm_exception(timeout_err)
    assert diag_to["category"] == "REQUEST_TIMEOUT"
    assert diag_to["is_transient"] is True


def test_llm_completion_transient_retry(monkeypatch):
    """Verifies transient error retry logic in generate_llm_completion."""
    mock_client = MagicMock()
    # First attempt fails with transient error, second attempt succeeds
    mock_client.chat.completions.create.side_effect = [
        APIConnectionError(request=MagicMock()),
        MagicMock(
            choices=[MagicMock(message=MagicMock(content="Success response", reasoning=None))],
            usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        )
    ]
    
    # Avoid real sleep in retries
    monkeypatch.setattr("time.sleep", lambda s: None)

    res = generate_llm_completion(prompt="Test prompt", override_client=mock_client)
    assert res["success"] is True
    assert res["content"] == "Success response"
    assert res["attempt"] == 2
