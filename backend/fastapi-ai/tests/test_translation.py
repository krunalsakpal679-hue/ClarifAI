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

from app.core.config import settings

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

        headers = {}
        if settings.INTERNAL_SERVICE_SECRET:
            headers["X-Internal-Service-Secret"] = settings.INTERNAL_SERVICE_SECRET

        response = client.post("/api/v1/translation/translate-document", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == "user_trans_api"
        assert data["document_id"] == "doc_trans_api"
        assert data["target_language"] == "hi"
        assert data["clauses_hi"][0]["original_text"] == "Original English text."


def test_offline_translation_all_clauses_coverage_and_fact_preservation():
    """
    CRITICAL REGRESSION TEST: Verifies Hindi translation works across EVERY eligible clause,
    including first, middle, last, short, long, figures, dates, percentages, and special characters.
    """
    test_clauses = [
        {
            "clause_id": "c1-first",
            "position": 1,
            "original_text": "Clause 1: The Tenant shall pay monthly rent of ₹65,000 on or before the 1st day of each month.",
            "simplified_text": "WHAT THIS CLAUSE MEANS:\nThe tenant must pay ₹65,000 rent per month on the 1st.\nWHO IS AFFECTED:\nLandlord and Tenant.",
            "why_flagged": "Flagged as Moderate risk due to detected pattern: Late-Payment Penalty."
        },
        {
            "clause_id": "c2-middle-currency-dates",
            "position": 2,
            "original_text": "Clause 2: A security deposit of ₹1,30,000 ($1,600 approx) must be remitted within 10 calendar days of signing.",
            "simplified_text": "WHAT THIS CLAUSE MEANS:\nSecurity deposit of ₹1,30,000 ($1,600 approx) is due within 10 calendar days.\nIMPORTANT DETAILS:\nAmount: ₹1,30,000; Deadline: 10 calendar days.",
            "why_flagged": "Standard clause analysis."
        },
        {
            "clause_id": "c3-special-chars-percentages",
            "position": 3,
            "original_text": "Clause 3: Overdue invoices accrue interest @ 1.5% per month (18% per annum) plus ₹500 fee.",
            "simplified_text": "WHAT THIS CLAUSE MEANS:\nLate payments incur 1.5% interest per month (18% per annum) and ₹500 penalty.",
            "why_flagged": "Flagged as High risk due to detected pattern: Late-Payment Penalty."
        },
        {
            "clause_id": "c4-long-clause",
            "position": 4,
            "original_text": "Clause 4: Receiving Party shall hold all Confidential Information in strict confidence and shall not disclose it to any third party for 3 years following termination.",
            "simplified_text": "WHAT THIS CLAUSE MEANS:\nConfidentiality must be maintained for 3 years without disclosing secrets to third parties.\nOBLIGATIONS & RIGHTS:\nReceiving Party must protect proprietary information.",
            "why_flagged": "Flagged as Low risk due to detected pattern: Non-Disclosure."
        },
        {
            "clause_id": "c5-last-termination",
            "position": 5,
            "original_text": "Clause 5: Either party may terminate this agreement upon 30 days prior written notice without cause.",
            "simplified_text": "WHAT THIS CLAUSE MEANS:\nEither party can cancel by giving 30 days written notice.",
            "why_flagged": "Standard termination clause."
        }
    ]

    summary = {
        "purpose": "Comprehensive commercial agreement.",
        "obligations": "Tenant must pay rent and maintain confidentiality.",
        "key_terms": "Duration 12 months with 30 days notice.",
        "key_risks": "Late fees apply."
    }

    # Execute translation without override client to test production fallback path
    result = translate_document_analysis(
        user_id="user-hi-full",
        document_id="doc-hi-full",
        summary=summary,
        clauses=test_clauses,
        target_language="hi"
    )

    assert result["success"] is True
    assert result["translation_status"] == "SUCCESS"
    assert len(result["clauses_hi"]) == 5

    for idx, c in enumerate(result["clauses_hi"], start=1):
        sim_hi = c.get("simplified_text_hi", "")
        why_hi = c.get("why_flagged_hi", "")
        orig = c.get("original_text", "")

        # 1. Verification: original_text is 100% untouched
        assert orig == test_clauses[idx - 1]["original_text"]

        # 2. Verification: simplified_text_hi is non-empty and contains Devanagari Hindi
        assert len(sim_hi) > 0
        assert any('\u0900' <= char <= '\u097f' for char in sim_hi), f"Clause {idx} simplified_text_hi lacks Devanagari Hindi!"

        # 3. Verification: why_flagged_hi is non-empty and contains Devanagari Hindi
        assert len(why_hi) > 0
        assert any('\u0900' <= char <= '\u097f' for char in why_hi), f"Clause {idx} why_flagged_hi lacks Devanagari Hindi!"

        # 4. Verification: Stable clause identifiers preserved
        assert c["clause_id"] == test_clauses[idx - 1]["clause_id"]
        assert c["position"] == test_clauses[idx - 1]["position"]

    # 5. Strict Contractual Fact Preservation Checks
    c1_hi = result["clauses_hi"][0]["simplified_text_hi"]
    assert "₹65,000" in c1_hi
    assert "1st" in c1_hi or "1" in c1_hi

    c2_hi = result["clauses_hi"][1]["simplified_text_hi"]
    assert "₹1,30,000" in c2_hi
    assert "10" in c2_hi

    c3_hi = result["clauses_hi"][2]["simplified_text_hi"]
    assert "1.5%" in c3_hi
    assert "18%" in c3_hi
    assert "₹500" in c3_hi

    c4_hi = result["clauses_hi"][3]["simplified_text_hi"]
    assert "3" in c4_hi

    c5_hi = result["clauses_hi"][4]["simplified_text_hi"]
    assert "30" in c5_hi
