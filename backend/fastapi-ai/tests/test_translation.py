"""
Multilingual English-to-Hindi Translation Unit Tests (AI-PHASE-MULTILINGUAL)
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.translation_service import (
    translate_text_to_hindi,
    translate_document_summary,
    translate_document_clauses,
    translate_document_analysis
)
from app.services.chatbot_service import (
    generate_chatbot_answer,
    HINDI_CONTROLLED_NO_ANSWER_RESPONSE,
    CONTROLLED_NO_ANSWER_RESPONSE
)
from app.services.qdrant_service import get_qdrant_client, index_document_clauses

client = TestClient(app)


def test_translate_text_to_hindi():
    """Verifies single text string translation using mock LLM."""
    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="यह एक कानूनी समझौता है।", reasoning=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=8, total_tokens=18)
    )

    hindi_out = translate_text_to_hindi("This is a legal agreement.", override_client=mock_llm_client)
    assert "कानूनी समझौता" in hindi_out or len(hindi_out) > 0


def test_original_text_is_never_altered_by_translation():
    """CRITICAL SECURITY/SAFETY TEST: Asserts that original_text is NEVER modified or translated."""
    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="अनुबंध की शर्तें हिंदी में।", reasoning=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=8, total_tokens=18)
    )

    original_verbatim_text = "Either party may terminate this agreement upon 30 days written notice."
    clauses = [
        {
            "clause_id": "c1",
            "position": 1,
            "original_text": original_verbatim_text,
            "simplified_text": "Either party can cancel with 30 days notice.",
            "why_flagged": "Standard termination clause."
        }
    ]

    translated_clauses = translate_document_clauses(clauses, override_client=mock_llm_client)

    assert len(translated_clauses) == 1
    t_clause = translated_clauses[0]
    
    # PROOF: original_text is verbatim identical
    assert t_clause["original_text"] == original_verbatim_text
    assert t_clause["original_text"] == "Either party may terminate this agreement upon 30 days written notice."
    assert "simplified_text_hi" in t_clause


def test_translation_failure_isolated_fallback():
    """Verifies per-document failure isolation: simulated LLM failure leaves English intact and marks TRANSLATION_UNAVAILABLE."""
    mock_failing_client = MagicMock()
    mock_failing_client.chat.completions.create.side_effect = RuntimeError("Groq translation timeout")

    summary_en = {
        "purpose": "Non-disclosure of confidential business information.",
        "obligations": "Recipient must protect secrets.",
        "key_terms": "5 years term.",
        "key_risks": "None."
    }

    clauses_en = [
        {
            "clause_id": "c1",
            "position": 1,
            "original_text": "Confidential information shall be kept secret.",
            "simplified_text": "Keep secret information private.",
            "why_flagged": "No risk."
        }
    ]

    res = translate_document_analysis(
        user_id="user_trans_fallback",
        document_id="doc_trans_fallback",
        summary=summary_en,
        clauses=clauses_en,
        target_language="hi",
        override_client=mock_failing_client
    )

    assert res["success"] is True
    assert res["translation_status"] == "TRANSLATION_UNAVAILABLE"
    # English summary & clauses preserved intact
    assert res["summary_hi"]["purpose"] == "Non-disclosure of confidential business information."
    assert res["clauses_hi"][0]["original_text"] == "Confidential information shall be kept secret."


def test_hindi_chatbot_identical_evidence_gating():
    """Verifies Hindi chatbot answer generation follows identical evidence gating rules as English."""
    memory_qdrant = get_qdrant_client(in_memory=True)
    user_id = "user_trans_chat"

    # 1. Unindexed/empty document -> Insufficient Evidence -> Returns Hindi Controlled No-Answer directly (NO LLM CALL)
    no_ans_res = generate_chatbot_answer(
        session_id="sess_hi_1",
        user_id=user_id,
        document_id="unindexed_doc_chat",
        question="What is the governing law of Mars?",
        target_language="hi",
        qdrant_client=memory_qdrant
    )
    assert no_ans_res["has_sufficient_evidence"] is False
    assert no_ans_res["answer"] == HINDI_CONTROLLED_NO_ANSWER_RESPONSE
    assert "असमर्थ" in no_ans_res["answer"]

    # 2. Supported Question -> Evidence Gate Passes -> Returns grounded answer with target_language='hi'
    doc_id = "doc_trans_chat"
    clauses = [
        {"clause_id": "c1", "position": 1, "text": "The agreement term is 3 years from the effective date.", "severity": "Safe"}
    ]
    index_document_clauses(user_id=user_id, document_id=doc_id, clauses=clauses, client=memory_qdrant)

    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="समझौते की अवधि प्रभावी तिथि से 3 वर्ष है।", reasoning=None))],
        usage=MagicMock(prompt_tokens=15, completion_tokens=10, total_tokens=25)
    )

    ans_res = generate_chatbot_answer(
        session_id="sess_hi_2",
        user_id=user_id,
        document_id=doc_id,
        question="What is the term of the agreement?",
        target_language="hi",
        qdrant_client=memory_qdrant,
        override_llm_client=mock_llm_client
    )
    assert ans_res["has_sufficient_evidence"] is True
    assert ans_res["target_language"] == "hi"
    assert "3 वर्ष" in ans_res["answer"]
    assert "c1" in ans_res["source_clause_ids"]


def test_translation_api_endpoint():
    """Verifies POST /api/v1/translation/translate-document router endpoint."""
    payload = {
        "user_id": "user_trans_api",
        "document_id": "doc_trans_api",
        "summary": {
            "purpose": "Agreement purpose.",
            "obligations": "Obligations summary.",
            "key_terms": "Key terms.",
            "key_risks": "None."
        },
        "clauses": [
            {
                "clause_id": "c1",
                "position": 1,
                "original_text": "Original English text.",
                "simplified_text": "Simplified English text.",
                "why_flagged": "No risk."
            }
        ],
        "target_language": "hi"
    }

    # Patch generate_llm_completion for endpoint test
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.services.translation_service.generate_llm_completion", lambda **k: {
            "success": True, "content": "अनुवादित हिंदी विवरण।", "model_name": "mock"
        })

        response = client.post("/api/v1/translation/translate-document", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == "user_trans_api"
        assert data["document_id"] == "doc_trans_api"
        assert data["target_language"] == "hi"
        assert data["clauses_hi"][0]["original_text"] == "Original English text."
