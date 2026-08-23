"""
BART-Base Summarization Service Unit Tests
"""

import pytest
from app.services.summarization_service import (
    get_summarization_model_name,
    get_summarization_status,
    summarize_text,
    BART_MAX_CONTEXT_TOKENS
)


def test_summarization_model_name():
    name = get_summarization_model_name()
    assert "bart" in name.lower()


def test_summarization_status():
    status = get_summarization_status()
    assert status["loaded"] is True
    assert status["max_context_tokens"] == 1024
    assert status["is_interim_placeholder"] is True
    assert status["fine_tuned_status"] == "IMPLEMENTATION DECISION REQUIRED"


def test_summarize_short_text():
    sample_text = (
        "This Agreement shall commence on January 1, 2026 and continue for a term of one year. "
        "Either party may terminate this agreement upon 30 days written notice to the other party."
    )
    res = summarize_text(sample_text, max_length=50, min_length=10)
    
    assert isinstance(res["summary"], str)
    assert len(res["summary"].strip()) > 0
    assert res["token_count"] <= 50
    assert res["is_chunked"] is False
    assert res["is_interim_placeholder"] is True


def test_summarize_chunked_long_text():
    # Long text exceeding 1024 tokens to trigger chunking strategy
    long_text = "This contract section details party responsibilities and liabilities. " * 150
    
    res = summarize_text(long_text, max_length=100, min_length=20)
    
    assert isinstance(res["summary"], str)
    assert len(res["summary"].strip()) > 0
    assert res["token_count"] <= 100
    assert res["is_chunked"] is True
    assert res["num_chunks_processed"] >= 2
