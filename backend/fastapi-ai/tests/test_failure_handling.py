"""
ClarifAI Failure Handling Logic Unit Tests (AI-MODEL-AVAILABILITY-FAILURE-01)
Verifies failure classification, secret key redaction, transient retry policy,
and no-fabrication / no-downgrade behavior per PRD v2.3 Section 56.20 and Decision R-08.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from groq import AuthenticationError, RateLimitError, APIConnectionError, NotFoundError

from app.services.llm_client import (
    generate_llm_completion,
    classify_llm_exception,
    sanitize_error_message,
    get_groq_client,
    STANDARD_USER_ERROR_MESSAGE
)
from app.services.risk_service import classify_clause_risk
from app.services.summarization_service import summarize_text


def test_standard_user_message_constant():
    assert STANDARD_USER_ERROR_MESSAGE == "AI processing is temporarily unavailable. Please try again later."


def test_secret_key_never_logged():
    fake_secret_key = "gsk_supersecret123456789key"
    os.environ["GROQ_API_KEY"] = fake_secret_key
    
    raw_error_text = f"Authentication error using key {fake_secret_key} on Groq endpoint"
    clean_text = sanitize_error_message(raw_error_text)
    
    assert fake_secret_key not in clean_text
    assert "gsk_***[REDACTED]***" in clean_text


def test_classify_auth_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {}
    
    err = AuthenticationError("Invalid API key provided", response=mock_resp, body=None)
    diag = classify_llm_exception(err)
    
    assert diag["category"] == "AUTH_FAILURE"
    assert diag["is_transient"] is False
    assert diag["user_message"] == STANDARD_USER_ERROR_MESSAGE
    assert diag["approved_fallback_exists"] is False


def test_classify_rate_limit_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}
    
    err = RateLimitError("Rate limit reached", response=mock_resp, body=None)
    diag = classify_llm_exception(err)
    
    assert diag["category"] == "QUOTA_OR_RATE_LIMIT_EXHAUSTED"
    assert diag["is_transient"] is True
    assert diag["approved_fallback_exists"] is False


def test_classify_not_found_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}
    
    err = NotFoundError("Model not found", response=mock_resp, body=None)
    diag = classify_llm_exception(err)
    
    assert diag["category"] == "MODEL_NOT_FOUND"
    assert diag["is_transient"] is False


def test_invalid_api_key_auth_failure_raises_structured_user_message():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {}
    mock_client.chat.completions.create.side_effect = AuthenticationError(
        "Invalid API Key", response=mock_resp, body=None
    )

    with pytest.raises(RuntimeError) as exc_info:
        generate_llm_completion("Test prompt", override_client=mock_client)

    assert STANDARD_USER_ERROR_MESSAGE in str(exc_info.value)
    assert "AUTH_FAILURE" in str(exc_info.value)
    # Auth error is non-transient -> Must attempt call exactly once
    assert mock_client.chat.completions.create.call_count == 1


def test_empty_prompt_raises_validation_error():
    with pytest.raises(ValueError) as exc_info:
        generate_llm_completion("   ")
    assert "must not be empty" in str(exc_info.value).lower()


def test_legal_bert_empty_input_raises():
    with pytest.raises(ValueError) as exc_info:
        classify_clause_risk("  ")
    assert "must not be empty" in str(exc_info.value).lower()


def test_legal_bert_never_defaults_to_safe_on_error():
    with patch("app.services.risk_service.load_legal_bert_model") as mock_load:
        mock_load.side_effect = RuntimeError("PyTorch CUDA Out of Memory")
        
        with pytest.raises(RuntimeError) as exc_info:
            classify_clause_risk("This clause contains high risk liability terms.")
            
        err_msg = str(exc_info.value)
        assert "AI risk classification failed" in err_msg
        assert "Out of Memory" in err_msg
        # Confirm error did NOT silently return severity "Safe"


def test_summarization_empty_input_raises():
    with pytest.raises(ValueError) as exc_info:
        summarize_text(" ")
    assert "must not be empty" in str(exc_info.value).lower()
