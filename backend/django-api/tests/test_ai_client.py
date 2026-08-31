"""
Phase 7 AI Service Integration Adapter Unit & Security Tests:
- Identical signature testing across all four functions (process_document, chat, compare, translate)
- Mixed success and per-clause-failure examples (PRD Task 5)
- No-answer chatbot case with legal framing disclaimer (PRD Task 5 & Ch. 56.38)
- Simulated AI-service-unavailable case (PRD Task 5 & Ch. 56.19)
- Schema and severity validation rejection (Ch. 49.3 & 56.9)
- Model failure & rate-limit exception handling (Ch. 56.19-56.21)
- Network retry policy (single retry on network drop only)
- Mock vs. Real configuration switch
"""
from unittest.mock import MagicMock, patch
from django.test import TestCase, override_settings
import requests

from services.ai_client import (
    AIServiceConnectionError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
    AIServiceValidationError,
    MockAIClient,
    RealAIClient,
    chat,
    compare,
    get_ai_client,
    process_document,
    translate,
)


class AIClientAdapterTestCase(TestCase):

    def test_mock_all_four_functions_happy_path(self):
        """MockAIClient returns valid schema-compliant structured responses for all 4 operations."""
        # 1. process_document
        res_proc = process_document("doc-123", "uploads/documents/doc-123.pdf")
        self.assertEqual(res_proc["document_id"], "doc-123")
        self.assertIn("summary", res_proc)
        self.assertEqual(len(res_proc["clauses"]), 4)
        self.assertIn(res_proc["clauses"][0]["severity"], ["high", "moderate", "low", "safe"])
        self.assertIn(res_proc["clauses"][0]["category"], [
            "Payment", "Termination", "Renewal", "Confidentiality",
            "Liability", "Intellectual Property", "Privacy", "Dispute Resolution"
        ])

        # 2. chat
        res_chat = chat("doc-123", "What are the payment terms?")
        self.assertIn("answer", res_chat)
        self.assertIn("NOT constitute legal advice", res_chat["answer"])
        self.assertIsInstance(res_chat["source_clause_ids"], list)

        # 3. compare
        res_comp = compare("doc-101", "doc-102")
        self.assertEqual(res_comp["document_a_id"], "doc-101")
        self.assertIn("changed", res_comp)

        # 4. translate
        res_trans = translate("doc-123", "hi")
        self.assertEqual(res_trans["target_lang"], "hi")
        self.assertIn("translated_content", res_trans)

    def test_mock_per_clause_failure_example(self):
        """MockAIClient includes a per-clause-failure example alongside successful clauses (Task 5)."""
        res = process_document("doc-123", "file.pdf")
        clauses = res["clauses"]

        # 3 successful clauses + 1 per-clause failure example
        failed_clause = next((c for c in clauses if c.get("status") == "clause_extraction_failed"), None)
        self.assertIsNotNone(failed_clause)
        self.assertEqual(failed_clause["clause_id"], "c-004")
        self.assertEqual(failed_clause["category"], "Dispute Resolution")
        self.assertIn("OCR degradation", failed_clause["simplified_text"])

    def test_mock_no_answer_chatbot_case(self):
        """MockAIClient includes a no-answer chatbot case with legal disclaimer (Task 5 & Ch. 56.38)."""
        # Test via simulation_mode='no_answer'
        client = MockAIClient(simulation_mode='no_answer')
        res = client.chat("doc-123", "What is the secret formula?")
        self.assertEqual(res["source_clause_ids"], [])
        self.assertIn("unable to find relevant information", res["answer"])
        self.assertIn("NOT constitute legal advice", res["answer"])

        # Test via unanswerable question message
        res_unanswerable = chat("doc-123", "unanswerable question about missing topic")
        self.assertEqual(res_unanswerable["source_clause_ids"], [])
        self.assertIn("unable to find relevant information", res_unanswerable["answer"])

    def test_mock_ai_service_unavailable_simulation(self):
        """MockAIClient raises AIServiceUnavailableError under simulation_mode='unavailable' (Task 5)."""
        client = MockAIClient(simulation_mode='unavailable')
        with self.assertRaises(AIServiceUnavailableError):
            client.process_document("doc-1", "file.pdf")

    def test_schema_and_severity_validation_rejection(self):
        """Malformed AI response (invalid severity enum) raises AIServiceValidationError."""
        mock_client = MockAIClient(simulation_mode='malformed')

        # Malformed clause severity ('extreme') fails validation
        with self.assertRaises(AIServiceValidationError):
            mock_client.process_document("doc-999", "file.pdf")

        # Malformed chat answer (empty) fails validation
        with self.assertRaises(AIServiceValidationError):
            mock_client.chat("doc-999", "Hello")

        # Malformed compare output fails validation
        with self.assertRaises(AIServiceValidationError):
            mock_client.compare("doc-1", "doc-2")

        # Malformed translate output fails validation
        with self.assertRaises(AIServiceValidationError):
            mock_client.translate("doc-1", "hi")

    def test_mock_simulation_failure_modes(self):
        """MockAIClient raises specific exception types under simulation modes."""
        # 1. Simulated network failure
        mock_net = MockAIClient(simulation_mode='network_failure')
        with self.assertRaises(AIServiceConnectionError):
            mock_net.process_document("doc-1", "file.pdf")

        # 2. Simulated rate limit / free-tier exhaustion
        mock_rl = MockAIClient(simulation_mode='rate_limit')
        with self.assertRaises(AIServiceRateLimitError):
            mock_rl.chat("doc-1", "Query")

        # 3. Simulated service unavailable
        mock_unavail = MockAIClient(simulation_mode='unavailable')
        with self.assertRaises(AIServiceUnavailableError):
            mock_unavail.compare("doc-1", "doc-2")

    @patch("requests.request")
    def test_real_client_single_network_retry_and_connection_error(self, mock_request):
        """RealAIClient performs exactly 1 single retry on network drop before raising AIServiceConnectionError."""
        # Simulate network connection drop on both initial attempt and single retry
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection refused by target")

        client = RealAIClient(base_url="http://localhost:8001")
        with self.assertRaises(AIServiceConnectionError):
            client.process_document("doc-100", "uploads/file.pdf")

        # Verify requests.request was called exactly twice (1 initial + 1 retry)
        self.assertEqual(mock_request.call_count, 2)

    @patch("requests.request")
    def test_real_client_http_status_exceptions(self, mock_request):
        """RealAIClient maps HTTP status codes to specific exception types without retrying HTTP errors."""

        # 1. HTTP 429 -> AIServiceRateLimitError
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_request.side_effect = [mock_resp_429]

        client = RealAIClient(base_url="http://localhost:8001")
        with self.assertRaises(AIServiceRateLimitError):
            client.chat("doc-1", "test query")
        self.assertEqual(mock_request.call_count, 1)  # Zero retries on HTTP 429

        # 2. HTTP 503 -> AIServiceUnavailableError
        mock_request.reset_mock()
        mock_resp_503 = MagicMock()
        mock_resp_503.status_code = 503
        mock_resp_503.text = "Service Unavailable"
        mock_request.side_effect = [mock_resp_503]

        with self.assertRaises(AIServiceUnavailableError):
            client.compare("doc-1", "doc-2")
        self.assertEqual(mock_request.call_count, 1)

        # 3. Request Timeout -> AIServiceTimeoutError
        mock_request.reset_mock()
        mock_request.side_effect = requests.exceptions.Timeout("Read timed out")

        with self.assertRaises(AIServiceTimeoutError):
            client.translate("doc-1", "hi")
        self.assertEqual(mock_request.call_count, 1)  # Zero retries on timeout

    @override_settings(AI_SERVICE_USE_MOCK=True)
    def test_factory_returns_mock_client(self):
        """get_ai_client returns MockAIClient instance when AI_SERVICE_USE_MOCK=True."""
        client = get_ai_client()
        self.assertIsInstance(client, MockAIClient)

    @override_settings(AI_SERVICE_USE_MOCK=False)
    def test_factory_returns_real_client(self):
        """get_ai_client returns RealAIClient instance when AI_SERVICE_USE_MOCK=False."""
        client = get_ai_client()
        self.assertIsInstance(client, RealAIClient)
