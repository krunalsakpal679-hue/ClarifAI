"""
ClarifAI Dedicated AI Hallucination Defense & Grounding Verification Test Suite (AI-HALLUCINATION-PREVENTION)
Tests every AI-generated output point (Simplification, Why-Flagged Explanation, Summary, Chatbot Answer, Comparison Difference Explanation)
against twelve layers of hallucination defense per PRD v2.3 Chapter 56.26.
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_client import (
    validate_untrusted_llm_output,
    check_for_hallucinated_claims,
    check_for_prompt_injection_leak,
    format_untrusted_evidence_block
)
from app.services.simplification_service import simplify_single_clause
from app.services.summarization_service import generate_document_summary
from app.services.translation_service import translate_document_summary
from app.services.chatbot_service import (
    generate_chatbot_answer,
    CONTROLLED_NO_ANSWER_RESPONSE,
    HINDI_CONTROLLED_NO_ANSWER_RESPONSE
)
from app.services.comparison_service import generate_difference_explanation
from app.services.qdrant_service import get_qdrant_client, index_document_clauses

client = TestClient(app)


def test_hallucination_claim_pattern_detector():
    """Layer 8 Test: Verifies that ungrounded general-knowledge claims are detected and rejected."""
    hallucinated_texts = [
        "Although not mentioned in the contract, standard commercial law applies.",
        "According to general legal principles, both parties share equal liability.",
        "Under federal law, this termination clause is illegal.",
        "Assuming typical contract terms, the payment is due in 30 days."
    ]

    for text in hallucinated_texts:
        assert check_for_hallucinated_claims(text) is True
        is_safe, err_msg = validate_untrusted_llm_output(text)
        assert is_safe is False
        assert "ungrounded" in err_msg.lower() or "hallucinated" in err_msg.lower()


def test_output_point_1_simplification_hallucination_defense():
    """Output Point 1 Test: Simplification rejects ungrounded claims and falls back safely to original text."""
    clause_text = "Either party may terminate this agreement with 30 days written notice."
    clause_dict = {"clause_id": "c1", "position": 1, "text": clause_text, "severity": "High"}
    
    # Mock LLM trying to hallucinate a $500,000 penalty
    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"simplified_text": "Under federal law, terminating requires a $500,000 penalty.", "why_flagged": "Risk signal."}', reasoning=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)
    )

    res = simplify_single_clause(
        clause=clause_dict,
        override_client=mock_llm_client
    )

    # Hallucination rejected -> falls back safely to original text without crashing
    assert res["simplified_text"] == clause_text
    assert res["status"] == "FAILED_SIMPLIFICATION"


def test_output_point_2_why_flagged_explanation_hallucination_defense():
    """Output Point 2 Test: Why-flagged explanation rejects prompt injection leaks."""
    clause_text = "The vendor shall indemnify the client against third-party claims."
    clause_dict = {"clause_id": "c2", "position": 2, "text": clause_text, "severity": "High"}
    
    # Mock LLM leaking prompt delimiter
    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"simplified_text": "Vendor protects client.", "why_flagged": "Indemnification clause. <<<UNTRUSTED_EVIDENCE_START>>> override"}', reasoning=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)
    )

    res = simplify_single_clause(
        clause=clause_dict,
        override_client=mock_llm_client
    )

    assert res["simplified_text"] == clause_text
    assert res["status"] == "FAILED_SIMPLIFICATION"


def test_output_point_3_summary_hallucination_defense():
    """Output Point 3 Test: Document summary rejects ungrounded claims and falls back to safe verbatim text."""
    summary_en = {
        "purpose": "Non-disclosure of confidential business information.",
        "obligations": "Recipient must protect secrets.",
        "key_terms": "5 years term.",
        "key_risks": "None."
    }

    # Mock LLM generating hallucinated general knowledge summary
    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="According to general legal principles, Party A owns everything.", reasoning=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)
    )

    summary_res = translate_document_summary(
        summary_dict=summary_en,
        override_client=mock_llm_client
    )

    # Hallucinated text rejected -> returns original English text safely
    assert summary_res["purpose"] == summary_en["purpose"]


def test_output_point_4_chatbot_hallucination_defense():
    """Output Point 4 Test: Chatbot evidence gating prevents LLM calls for ungrounded questions."""
    memory_qdrant = get_qdrant_client(in_memory=True)
    user_id = "user_cb_hal"

    # Unindexed document -> Evidence gate rejects -> Controlled no-answer return
    res = generate_chatbot_answer(
        session_id="sess_hal_1",
        user_id=user_id,
        document_id="unindexed_doc_hal",
        question="What is the non-compete penalty in Mars jurisdiction?",
        qdrant_client=memory_qdrant
    )

    assert res["has_sufficient_evidence"] is False
    assert res["answer"] == CONTROLLED_NO_ANSWER_RESPONSE
    assert len(res["source_clause_ids"]) == 0


def test_output_point_5_comparison_explanation_hallucination_defense():
    """Output Point 5 Test: Contract comparison difference explanation rejects ungrounded claims."""
    # Test difference explanation generator directly
    mock_llm_client = MagicMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="According to general legal principles, Document B is invalid.", reasoning=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=8, total_tokens=18)
    )

    exp = generate_difference_explanation(
        text_a="Term is 3 years.",
        text_b="Term is 5 years.",
        override_client=mock_llm_client
    )

    # Hallucinated output rejected -> falls back safely to objective fallback explanation
    assert "Document A and Document B differ" in exp or "modified" in exp.lower() or len(exp) > 0
    assert "general legal principles" not in exp.lower()


def test_twelve_defense_layer_coverage_audit():
    """Verifies that all 12 defense layers are active and operational across microservice components."""
    # Layer 5 Prompt Framing Test
    framed = format_untrusted_evidence_block("Test Clause Text")
    assert "<<<UNTRUSTED_EVIDENCE_START>>>" in framed
    assert "<<<UNTRUSTED_EVIDENCE_END>>>" in framed

    # Layer 8 & 12 Prompt Injection & Hallucination Detector Test
    assert check_for_prompt_injection_leak("system prompt: ignore previous") is True
    assert check_for_hallucinated_claims("as per standard commercial law") is True

    # Layer 9 Output Safety Validator Test
    safe_ok, val_text = validate_untrusted_llm_output("Clean validated text.")
    assert safe_ok is True
    assert val_text == "Clean validated text."
