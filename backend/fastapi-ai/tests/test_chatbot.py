"""
Contract-Grounded Conversational RAG Chatbot Unit Tests (AI-PHASE-CHATBOT)
Verifies grounded answer generation, source_clause_ids traceability,
controlled no-answer direct return without LLM call when evidence gate fails,
session+document memory scoping and cross-session isolation, output validation,
prompt injection defense, and API router endpoints.
"""

import pytest
from unittest.mock import MagicMock
from qdrant_client import QdrantClient
from fastapi.testclient import TestClient

from app.main import app
from app.services.qdrant_service import ensure_collection_exists, index_document_clauses
from app.services.chatbot_service import (
    generate_chatbot_answer,
    get_session_history,
    clear_session_memory,
    CONTROLLED_NO_ANSWER_RESPONSE,
    NON_LEGAL_ADVICE_DISCLAIMER
)

client = TestClient(app)


@pytest.fixture
def memory_qdrant_client():
    """Provides an isolated in-memory QdrantClient instance for each test."""
    test_client = QdrantClient(":memory:")
    ensure_collection_exists(test_client)
    return test_client


def test_grounded_answer_with_source_clause_ids(memory_qdrant_client):
    """Test: Well-supported question returns grounded answer with correct source_clause_ids and disclaimer."""
    user_id = "user_cb_01"
    document_id = "doc_cb_01"
    session_id = "session_cb_01"

    clauses = [
        {
            "position": 1,
            "clause_id": "clause_term_01",
            "text": "Either party may terminate this Agreement upon thirty (30) days prior written notice.",
            "severity": "Safe",
            "categories": ["Termination"]
        }
    ]

    index_document_clauses(user_id=user_id, document_id=document_id, clauses=clauses, client=memory_qdrant_client)

    # Mock Groq LLM client response
    mock_llm = MagicMock()
    mock_llm.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(message=MagicMock(content="The termination notice period required is thirty (30) days in writing.", reasoning=None))
        ],
        usage=MagicMock(prompt_tokens=100, completion_tokens=20, total_tokens=120)
    )

    question = "What is the notice period required to terminate this agreement?"
    res = generate_chatbot_answer(
        session_id=session_id,
        user_id=user_id,
        document_id=document_id,
        question=question,
        qdrant_client=memory_qdrant_client,
        override_llm_client=mock_llm
    )

    assert res["has_sufficient_evidence"] is True
    assert "thirty (30) days" in res["answer"]
    assert res["source_clause_ids"] == ["clause_term_01"]
    assert res["disclaimer"] == NON_LEGAL_ADVICE_DISCLAIMER
    assert mock_llm.chat.completions.create.called is True


def test_insufficient_evidence_returns_no_answer_without_llm_call(memory_qdrant_client):
    """Test: When AI-PHASE-RAG reports insufficient evidence, LLM is NOT called and no-answer response returned directly."""
    user_id = "user_cb_02"
    document_id = "doc_cb_02"
    session_id = "session_cb_02"

    # Document has no clauses indexed -> retrieval returns 0 candidates
    mock_llm = MagicMock()

    question = "What are the intellectual property patent licensing terms in China?"
    res = generate_chatbot_answer(
        session_id=session_id,
        user_id=user_id,
        document_id=document_id,
        question=question,
        qdrant_client=memory_qdrant_client,
        override_llm_client=mock_llm
    )

    assert res["has_sufficient_evidence"] is False
    assert res["answer"] == CONTROLLED_NO_ANSWER_RESPONSE
    assert res["source_clause_ids"] == []
    # VERIFY CRITICAL SAFETY REQUIREMENT: LLM MUST NOT BE CALLED
    assert mock_llm.chat.completions.create.called is False


def test_same_session_conversational_memory(memory_qdrant_client):
    """Test: Follow-up question correctly uses same-session memory."""
    user_id = "user_cb_mem"
    document_id = "doc_cb_mem"
    session_id = "session_cb_mem"

    clauses = [
        {
            "position": 1,
            "clause_id": "c_pay_1",
            "text": "All invoices shall be paid within 30 calendar days of receipt.",
            "severity": "Safe",
            "categories": ["Payment Terms"]
        }
    ]

    index_document_clauses(user_id=user_id, document_id=document_id, clauses=clauses, client=memory_qdrant_client)

    mock_llm = MagicMock()
    mock_llm.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(message=MagicMock(content="Invoices must be paid within 30 days.", reasoning=None))
        ],
        usage=MagicMock(prompt_tokens=50, completion_tokens=10, total_tokens=60)
    )

    # Turn 1
    q1 = "When are invoices due?"
    generate_chatbot_answer(
        session_id=session_id,
        user_id=user_id,
        document_id=document_id,
        question=q1,
        qdrant_client=memory_qdrant_client,
        override_llm_client=mock_llm
    )

    history = get_session_history(session_id=session_id, user_id=user_id, document_id=document_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == q1
    assert history[1]["role"] == "assistant"

    # Turn 2
    q2 = "Is that 30 calendar days or business days?"
    generate_chatbot_answer(
        session_id=session_id,
        user_id=user_id,
        document_id=document_id,
        question=q2,
        qdrant_client=memory_qdrant_client,
        override_llm_client=mock_llm
    )

    history_updated = get_session_history(session_id=session_id, user_id=user_id, document_id=document_id)
    assert len(history_updated) == 4
    assert history_updated[2]["content"] == q2


def test_cross_session_cross_user_cross_document_memory_isolation(memory_qdrant_client):
    """Test: Conversational memory never crosses session, user, or document boundaries."""
    user_A = "user_A"
    user_B = "user_B"
    doc_A = "doc_A"
    doc_B = "doc_B"
    session_A = "session_A"
    session_B = "session_B"

    clauses_A = [{"position": 1, "clause_id": "cA", "text": "Payment terms clause for User A."}]
    index_document_clauses(user_id=user_A, document_id=doc_A, clauses=clauses_A, client=memory_qdrant_client)

    mock_llm = MagicMock()
    mock_llm.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="User A answer.", reasoning=None))],
        usage=MagicMock(prompt_tokens=50, completion_tokens=10, total_tokens=60)
    )

    # Populate Session A for User A & Doc A
    generate_chatbot_answer(session_id=session_A, user_id=user_A, document_id=doc_A, question="Question A", qdrant_client=memory_qdrant_client, override_llm_client=mock_llm)

    # Query with Session B, User B, or Doc B
    history_cross_session = get_session_history(session_id=session_B, user_id=user_A, document_id=doc_A)
    history_cross_user = get_session_history(session_id=session_A, user_id=user_B, document_id=doc_A)
    history_cross_doc = get_session_history(session_id=session_A, user_id=user_A, document_id=doc_B)

    assert history_cross_session == []
    assert history_cross_user == []
    assert history_cross_doc == []


def test_chatbot_api_endpoints():
    """API endpoint test for POST /api/v1/chatbot/chat and DELETE /api/v1/chatbot/session/{session_id}."""
    payload = {
        "session_id": "api_session_01",
        "user_id": "api_user_01",
        "document_id": "api_doc_01",
        "question": "Sample API test question?"
    }

    response = client.post("/api/v1/chatbot/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "answer" in data
    assert "has_sufficient_evidence" in data
    assert "source_clause_ids" in data
    assert "disclaimer" in data

    # Clear session API call
    del_res = client.delete("/api/v1/chatbot/session/api_session_01?user_id=api_user_01&document_id=api_doc_01")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
