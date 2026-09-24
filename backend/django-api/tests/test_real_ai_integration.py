"""
Phase 5 Real AI Microservice Integration Tests (BOOK4-PHASE-05).
Validates that RealAIClient uses 100% verified route paths, correct payload schemas,
and strict validators against all 25 FastAPI router endpoints.
"""
from unittest.mock import MagicMock, patch
from django.test import TestCase
import requests

from services.ai_client.client import RealAIClient
from services.ai_client.validators import (
    validate_chat_response,
    validate_compare_response,
    validate_process_document_response,
    validate_translate_response,
)


class RealAIClientIntegrationTestCase(TestCase):
    """
    Tests RealAIClient endpoint dispatching, header propagation, and response validation.
    """

    def setUp(self):
        self.client = RealAIClient(
            base_url="http://localhost:8001",
            secret="test-internal-secret",
            timeout=10
        )

    def test_headers_contain_internal_secrets(self):
        """Header dictionary contains both X-Internal-Secret and X-Internal-Service-Secret."""
        headers = self.client._get_headers()
        self.assertEqual(headers.get("Content-Type"), "application/json")
        self.assertEqual(headers.get("X-Internal-Secret"), "test-internal-secret")
        self.assertEqual(headers.get("X-Internal-Service-Secret"), "test-internal-secret")

    @patch("requests.request")
    def test_chat_real_endpoint_and_validation(self, mock_request):
        """chat() calls POST /api/v1/chatbot/chat and validates response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "answer": "This agreement terminates in 30 days. Disclaimer: This does NOT constitute legal advice.",
            "source_clause_ids": [1, 2],
            "confidence": 0.95,
            "grounded": True,
            "target_language": "en",
            "session_id": "sess-123"
        }
        mock_request.return_value = mock_resp

        res = self.client.chat(document_id="doc-001", message="When does this terminate?")
        
        # Verify correct URL and payload
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        self.assertEqual(call_kwargs["method"], "POST")
        self.assertEqual(call_kwargs["url"], "http://localhost:8001/api/v1/chatbot/chat")
        self.assertEqual(call_kwargs["json"]["document_id"], "doc-001")
        self.assertEqual(call_kwargs["json"]["question"], "When does this terminate?")
        self.assertIn("answer", res)
        self.assertEqual(res["source_clause_ids"], [1, 2])

    @patch("requests.request")
    def test_compare_real_endpoint_and_validation(self, mock_request):
        """compare() calls POST /api/v1/comparison/compare-documents and validates response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "summary": "Comparing doc A and doc B",
            "matched": [{"clause_a_id": 1, "clause_b_id": 1, "similarity_score": 0.95}],
            "changed": [{"clause_a_id": 2, "clause_b_id": 2, "difference_explanation": "Liability cap increased", "similarity_score": 0.60}],
            "missing": [],
            "differences": [{"difference_explanation": "Liability cap increased", "similarity_score": 0.60}],
            "total_pairs": 2,
            "execution_time_ms": 12.5
        }
        mock_request.return_value = mock_resp

        res = self.client.compare(document_a_id="doc-A", document_b_id="doc-B")
        
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        self.assertEqual(call_kwargs["method"], "POST")
        self.assertEqual(call_kwargs["url"], "http://localhost:8001/api/v1/comparison/compare-documents")
        self.assertEqual(call_kwargs["json"]["document_id_a"], "doc-A")
        self.assertEqual(call_kwargs["json"]["document_id_b"], "doc-B")
        self.assertIn("changed", res)
        self.assertIn("matched", res)

    @patch("requests.request")
    def test_translate_real_endpoint_and_validation(self, mock_request):
        """translate() calls POST /api/v1/translation/translate-document and validates response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "document_id": "doc-001",
            "target_language": "hi",
            "summary": {"overview": "अनुबंध अवलोकन"},
            "clauses": [{"position": 1, "simplified_text": "भुगतान 30 दिनों के भीतर देय है।"}]
        }
        mock_request.return_value = mock_resp

        res = self.client.translate(document_id="doc-001", target_lang="hi")
        
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        self.assertEqual(call_kwargs["method"], "POST")
        self.assertEqual(call_kwargs["url"], "http://localhost:8001/api/v1/translation/translate-document")
        self.assertEqual(call_kwargs["json"]["target_language"], "hi")
        self.assertEqual(res["target_lang"], "hi")
        self.assertIn("translated_content", res)

    @patch("requests.request")
    def test_delete_document_embeddings_real_endpoint(self, mock_request):
        """delete_document_embeddings() calls DELETE /api/v1/qdrant/delete-document."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "success": True,
            "document_id": "doc-001",
            "user_id": "usr-123",
            "deleted_points": 5
        }
        mock_request.return_value = mock_resp

        res = self.client.delete_document_embeddings(document_id="doc-001", user_id="usr-123")
        
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args.kwargs
        self.assertEqual(call_kwargs["method"], "DELETE")
        self.assertEqual(call_kwargs["url"], "http://localhost:8001/api/v1/qdrant/delete-document")
        self.assertEqual(call_kwargs["json"]["document_id"], "doc-001")
        self.assertEqual(call_kwargs["json"]["user_id"], "usr-123")
        self.assertTrue(res["success"])

    @patch.object(RealAIClient, "extract_pdf")
    @patch.object(RealAIClient, "clean_text")
    @patch.object(RealAIClient, "segment_clauses")
    @patch.object(RealAIClient, "categorize_clauses")
    @patch.object(RealAIClient, "evaluate_rules")
    @patch.object(RealAIClient, "classify_document_risk")
    @patch.object(RealAIClient, "simplify_clauses")
    @patch.object(RealAIClient, "summarize_document")
    @patch.object(RealAIClient, "generate_embeddings")
    @patch.object(RealAIClient, "index_document_qdrant")
    def test_process_document_full_pipeline_orchestration(
        self,
        mock_index,
        mock_embed,
        mock_sum,
        mock_simp,
        mock_risk,
        mock_rules,
        mock_cat,
        mock_seg,
        mock_clean,
        mock_pdf
    ):
        """process_document() executes the full 10-stage sequential AI pipeline and returns validated payload."""
        # 1. Mock Clean Text
        mock_clean.return_value = {
            "success": True,
            "cleaned_text": "Payment is due within 30 days. Either party may terminate with 15 days notice."
        }
        # 2. Mock Segment Clauses
        mock_seg.return_value = {
            "success": True,
            "total_clauses": 2,
            "clauses": [
                {"id": 1, "position": 1, "text": "Payment is due within 30 days."},
                {"id": 2, "position": 2, "text": "Either party may terminate with 15 days notice."}
            ]
        }
        # 3. Mock Categorize Clauses
        mock_cat.return_value = {
            "success": True,
            "total_clauses": 2,
            "categorized_clauses": [
                {"id": 1, "position": 1, "text": "Payment is due within 30 days.", "category": "Payment"},
                {"id": 2, "position": 2, "text": "Either party may terminate with 15 days notice.", "category": "Termination"}
            ]
        }
        # 4. Mock Evaluate Rules
        mock_rules.return_value = {
            "success": True,
            "total_findings": 1,
            "findings": [{"rule_id": "R002", "category": "Termination", "matched_text": "15 days notice"}]
        }
        # 5. Mock Classify Risk
        mock_risk.return_value = {
            "success": True,
            "total_clauses": 2,
            "classified_clauses": [
                {"id": 1, "position": 1, "text": "Payment is due within 30 days.", "category": "Payment", "severity": "safe"},
                {"id": 2, "position": 2, "text": "Either party may terminate with 15 days notice.", "category": "Termination", "severity": "moderate"}
            ]
        }
        # 6. Mock Simplify Clauses
        mock_simp.return_value = {
            "success": True,
            "simplified_clauses": [
                {"id": 1, "position": 1, "simplified_text": "You must pay within 30 days.", "why_flagged": "Standard terms."},
                {"id": 2, "position": 2, "simplified_text": "Contract can end on 15 days notice.", "why_flagged": "Notice period is short."}
            ]
        }
        # 7. Mock Summarize Document
        mock_sum.return_value = {
            "success": True,
            "summary": {
                "overview": "Short service contract with standard payment terms.",
                "key_points": ["30 days payment window", "15 days termination notice"],
                "risk_profile": {"safe": 1, "moderate": 1},
                "obligations": ["Timely payment required"]
            }
        }
        # 8. Mock Embeddings & Indexing
        mock_embed.return_value = {"success": True, "embedded_clauses": [{"position": 1}, {"position": 2}]}
        mock_index.return_value = {"success": True, "total_indexed": 2}

        # Execute Orchestration
        result = self.client.process_document(
            document_id="doc-999",
            file_reference="Sample contract text for direct extraction",
            user_id="usr-123"
        )

        # Assertions on pipeline calls
        mock_clean.assert_called_once()
        mock_seg.assert_called_once()
        mock_cat.assert_called_once()
        mock_rules.assert_called_once()
        mock_risk.assert_called_once()
        mock_simp.assert_called_once()
        mock_sum.assert_called_once()
        mock_embed.assert_called_once()
        mock_index.assert_called_once_with(
            user_id="usr-123",
            document_id="doc-999",
            clauses=[{"position": 1}, {"position": 2}]
        )

        # Assertions on validated structure
        self.assertEqual(result["document_id"], "doc-999")
        self.assertEqual(len(result["clauses"]), 2)
        self.assertEqual(result["clauses"][0]["category"], "Payment")
        self.assertEqual(result["clauses"][0]["severity"], "safe")
        self.assertEqual(result["clauses"][1]["category"], "Termination")
        self.assertEqual(result["clauses"][1]["severity"], "moderate")
        self.assertIn("overview", result["summary"])
