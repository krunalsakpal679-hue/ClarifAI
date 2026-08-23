"""
Multilingual-E5 Embedding Service Unit Tests
"""

import pytest
from app.services.embedding_service import (
    get_embedding_model_name,
    get_embedding_dimension,
    generate_clause_embedding,
    generate_query_embedding,
    get_embedding_status
)


def test_embedding_model_name():
    name = get_embedding_model_name()
    assert "multilingual-e5" in name.lower()


def test_embedding_dimension():
    dim = get_embedding_dimension()
    assert dim == 768


def test_english_and_hindi_clause_embeddings():
    en_clause = "This Agreement shall be governed by the laws of the State of California."
    hi_clause = "यह समझौता कैलिफोर्निया राज्य के कानूनों द्वारा शासित होगा।"

    en_vector = generate_clause_embedding(en_clause)
    hi_vector = generate_clause_embedding(hi_clause)

    # Verify fixed-length non-empty vectors
    assert len(en_vector) == 768
    assert len(hi_vector) == 768

    # Verify elements are valid floats
    assert isinstance(en_vector[0], float)
    assert isinstance(hi_vector[0], float)


def test_query_embedding():
    query_text = "What is the termination notice period?"
    query_vector = generate_query_embedding(query_text)

    assert len(query_vector) == 768
    assert isinstance(query_vector[0], float)


def test_embedding_status():
    status = get_embedding_status()
    assert status["loaded"] is True
    assert status["vector_dimension"] == 768
    assert status["is_interim_placeholder"] is True
    assert status["fine_tuned_status"] == "IMPLEMENTATION DECISION REQUIRED"
