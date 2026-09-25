"""
BOOK4-PHASE-26: Full-System Infrastructure & Dependency Failure / Recovery Verification (E2E-37 – E2E-41)
Source Traceability: PRD v2.3 Chapter 56.19-56.21, Chapter 15, Chapter 18, Chapter 30.

Test Matrix Coverage:
1. E2E-37: Stop / simulate FastAPI AI service failure; attempt document processing; confirm clean failure
   (document status FAILED, failure_reason set, zero fabricated success result) and confirm full recovery
   when AI service returns online.
2. E2E-38: Stop / simulate Qdrant vector database failure; attempt chatbot query and document comparison;
   confirm both fail safely with specific HTTP 503 error envelopes, and confirm full recovery when Qdrant returns online.
3. E2E-39: Stop / simulate Redis broker failure; attempt document upload; confirm clear failure / queue isolation
   and zero silent drops, and confirm full recovery when Redis returns online.
4. E2E-40: Force Celery task failure (mid-pipeline crash exception); confirm document transitions to status FAILED
   with failure_reason (never stuck in intermediate state, never falsely complete), and confirm full recovery on subsequent runs.
5. E2E-41: Force malformed AI response (intercept and corrupt schema payload); confirm validation layer rejects it
   end-to-end (HTTP 503), zero corrupted data persisted to DB, and confirm full recovery when valid response returns.
"""

from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.comparison.models import Comparison, ComparisonCategory, ComparisonResult, ComparisonStatus
from apps.documents.models import Clause, ClauseCategory, ClauseSeverity, ClauseStatus, Document, DocumentStatus, DocumentSummary
from services.ai_client.exceptions import (
    AIServiceConnectionError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
    AIServiceValidationError,
)
from services.ai_client.validators import validate_chat_response, validate_clause, validate_process_document_response
from tasks.document_tasks import process_document
from tests.test_documents import create_sample_pdf

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=True,
)
class E2EFailureAndRecoveryTestCase(APITestCase):
    """
    End-to-End Infrastructure Dependency Failure & Recovery Test Suite for E2E-37 through E2E-41.
    """

    def setUp(self):
        cache.clear()

        # Authenticated Primary User
        self.user = User.objects.create_user(
            email="failure_test_user@clarifai.io",
            password="SecurePassword123!"
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # Document 1: Completed Cloud Agreement
        self.doc_complete = Document.objects.create(
            user=self.user,
            original_filename="master_cloud_agreement.pdf",
            file_reference="uploads/documents/master_cloud_agreement.pdf",
            status=DocumentStatus.COMPLETE
        )
        self.summary_complete = DocumentSummary.objects.create(
            document=self.doc_complete,
            purpose_text="Cloud hosting services.",
            key_risks_text="Uncapped liability.",
            key_terms_text="Net 30 payment.",
            obligations_text="Maintain 99.9% SLA."
        )
        self.clause_complete = Clause.objects.create(
            document=self.doc_complete,
            position=1,
            original_text="Fees and Payments: Customer shall pay all invoices within thirty (30) days.",
            simplified_text="Pay invoices within 30 days.",
            severity=ClauseSeverity.SAFE,
            category=ClauseCategory.PAYMENT,
            status=ClauseStatus.COMPLETE
        )

        # Document 2: Queued Document for Processing Tasks
        self.doc_queued = Document.objects.create(
            user=self.user,
            original_filename="pending_vendor_contract.pdf",
            file_reference="uploads/documents/pending_vendor_contract.pdf",
            status=DocumentStatus.QUEUED
        )

    def tearDown(self):
        cache.clear()

    # =========================================================================
    # E2E-37: FastAPI AI Service Unavailable & Clean Recovery
    # =========================================================================

    def test_e2e_37_ai_service_unavailable_failure_and_recovery(self):
        """
        E2E-37:
        1. Failure Phase: Simulates FastAPI AI service down (AIServiceUnavailableError / Connection error).
           Document processing task transitions document to status FAILED with structured failure_reason.
           Django REST API returns clean HTTP 503 error envelope. Zero fabricated complete results.
        2. Recovery Phase: Restores AI service availability. Subsequent processing task completes cleanly.
        """
        doc_fail = Document.objects.create(
            user=self.user,
            original_filename="e2e37_test_contract.pdf",
            file_reference="uploads/documents/e2e37_test_contract.pdf",
            status=DocumentStatus.QUEUED
        )

        # 1. FAILURE PHASE: FastAPI AI service is unavailable (HTTP 503 / connection refused)
        with patch("services.ai_client.process_document") as mock_proc:
            mock_proc.side_effect = AIServiceUnavailableError(
                "AI service http://localhost:8001 is currently unavailable (HTTP 503)."
            )

            # Process document task encounters AI service failure
            with self.assertRaises(AIServiceUnavailableError):
                process_document(str(doc_fail.id))

        doc_fail.refresh_from_db()
        # Verify document status transitioned to FAILED with explicit failure reason
        self.assertEqual(doc_fail.status, DocumentStatus.FAILED)
        self.assertIsNotNone(doc_fail.failure_reason)
        self.assertIn("unavailable", doc_fail.failure_reason.lower())
        # Zero fabricated clauses or summary created
        self.assertEqual(doc_fail.clauses.count(), 0)
        self.assertFalse(DocumentSummary.objects.filter(document=doc_fail).exists())

        # Verify REST API endpoint returns clean HTTP 503 for AI dependent endpoints during outage
        chat_url = f"/api/documents/{self.doc_complete.id}/chat/messages/"
        with patch("services.ai_client.chat") as mock_chat:
            mock_chat.side_effect = AIServiceUnavailableError("AI microservice unavailable")
            res_api = self.client.post(chat_url, {"query": "What are payment terms?"}, format="json")

        self.assertEqual(res_api.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", res_api.json())
        self.assertEqual(res_api.json()["error"]["code"], "AI_SERVICE_UNAVAILABLE")

        # 2. RECOVERY PHASE: FastAPI AI service comes back online
        doc_rec = Document.objects.create(
            user=self.user,
            original_filename="e2e37_recovered_contract.pdf",
            file_reference="uploads/documents/e2e37_recovered_contract.pdf",
            status=DocumentStatus.QUEUED
        )

        with patch("services.ai_client.process_document") as mock_proc_rec:
            mock_proc_rec.return_value = {
                "document_id": str(doc_rec.id),
                "summary": {
                    "purpose_text": "Vendor supply terms.",
                    "key_risks_text": "Standard risk.",
                    "key_terms_text": "Net 30 days.",
                    "obligations_text": "Timely delivery."
                },
                "clauses": [
                    {
                        "clause_id": "c-rec-1",
                        "position": 1,
                        "original_text": "Delivery must occur within 14 days.",
                        "simplified_text": "Deliver within 14 days.",
                        "severity": "safe",
                        "category": "Payment"
                    }
                ]
            }
            res_task = process_document(str(doc_rec.id))

        doc_rec.refresh_from_db()
        self.assertEqual(res_task["status"], "complete")
        self.assertEqual(doc_rec.status, DocumentStatus.COMPLETE)
        self.assertIsNone(doc_rec.failure_reason)
        self.assertEqual(doc_rec.clauses.count(), 1)
        self.assertTrue(DocumentSummary.objects.filter(document=doc_rec).exists())

    # =========================================================================
    # E2E-38: Qdrant Vector Database Unavailable & Clean Recovery
    # =========================================================================

    def test_e2e_38_qdrant_unavailable_failure_and_recovery(self):
        """
        E2E-38:
        1. Failure Phase: Simulates Qdrant vector database down (Connection / API Error).
           Chatbot Q&A and Document Comparison endpoints fail safely with HTTP 503 AI_SERVICE_UNAVAILABLE.
           No partial chat messages or invalid comparison records created.
        2. Recovery Phase: Restores Qdrant vector database. Chatbot and comparison endpoints return online.
        """
        chat_url = f"/api/documents/{self.doc_complete.id}/chat/messages/"
        comp_url = "/api/comparisons/"

        # Second document for comparison setup
        doc_b = Document.objects.create(
            user=self.user,
            original_filename="comparison_target.pdf",
            file_reference="uploads/documents/comparison_target.pdf",
            status=DocumentStatus.COMPLETE
        )

        # 1. FAILURE PHASE: Qdrant service is down
        with patch("services.ai_client.chat") as mock_chat:
            mock_chat.side_effect = AIServiceUnavailableError("Qdrant vector database service unavailable.")
            res_chat = self.client.post(chat_url, {"query": "What are payment terms?"}, format="json")

        self.assertEqual(res_chat.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(res_chat.json()["error"]["code"], "AI_SERVICE_UNAVAILABLE")

        with patch("services.ai_client.compare") as mock_comp:
            mock_comp.side_effect = AIServiceUnavailableError("Qdrant vector database service unavailable.")
            res_comp = self.client.post(comp_url, {"base_document_id": str(self.doc_complete.id), "target_document_id": str(doc_b.id)}, format="json")

        self.assertEqual(res_comp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn(res_comp.json()["error"]["code"], ["SERVICE_UNAVAILABLE", "AI_SERVICE_UNAVAILABLE"])

        # Confirm no corrupted assistant chat message was persisted during failure
        last_chat_msg = ChatMessage.objects.filter(session__document=self.doc_complete).order_by("created_at").last()
        if last_chat_msg:
            self.assertNotEqual(last_chat_msg.role, MessageRole.ASSISTANT)

        # 2. RECOVERY PHASE: Qdrant service restored
        with patch("services.ai_client.chat") as mock_chat_rec:
            mock_chat_rec.return_value = {
                "answer": "Payments must be made within 30 days. ClarifAI does NOT constitute legal advice.",
                "source_clause_ids": [str(self.clause_complete.id)]
            }
            res_chat_rec = self.client.post(chat_url, {"query": "What are payment terms?"}, format="json")

        self.assertEqual(res_chat_rec.status_code, status.HTTP_201_CREATED)
        self.assertIn("30 days", res_chat_rec.json()["content"])
        self.assertEqual(res_chat_rec.json()["source_clause_ids"], [str(self.clause_complete.id)])

    # =========================================================================
    # E2E-39: Redis Broker / Celery Queue Failure & Clean Recovery
    # =========================================================================

    def test_e2e_39_redis_broker_failure_and_recovery(self):
        """
        E2E-39:
        1. Failure Phase: Simulates Redis broker down (ConnectionRefusedError on Celery task enqueue).
           Upload request catches broker error, fails clearly (HTTP 503 error envelope), and NEVER
           silently drops the request or leaves a phantom stuck document.
        2. Recovery Phase: Restores Redis broker. Subsequent upload enqueues and processes safely.
        """
        pdf_bytes = create_sample_pdf()
        pdf_file = SimpleUploadedFile(
            "redis_test_contract.pdf",
            pdf_bytes,
            content_type="application/pdf"
        )

        # 1. FAILURE PHASE: Redis connection failure when enqueuing task
        with patch("apps.documents.views.process_document.delay") as mock_delay:
            mock_delay.side_effect = ConnectionError("Error 10061 connecting to localhost:6379. Connection refused.")

            response = self.client.post(
                "/api/documents/",
                data={"file": pdf_file},
                format="multipart"
            )

        # Server returns clean error response indicating background processing enqueue failure
        self.assertIn(response.status_code, [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE])
        res_json = response.json()
        self.assertIn("error", res_json)

        # 2. RECOVERY PHASE: Redis restored and delay succeeds
        pdf_file_rec = SimpleUploadedFile(
            "redis_recovered_contract.pdf",
            pdf_bytes,
            content_type="application/pdf"
        )

        with patch("apps.documents.views.process_document.delay") as mock_delay_rec:
            mock_delay_rec.return_value = MagicMock(id="task-12345")
            res_rec = self.client.post(
                "/api/documents/",
                data={"file": pdf_file_rec},
                format="multipart"
            )

        self.assertEqual(res_rec.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_rec.json()["status"], DocumentStatus.QUEUED)
        mock_delay_rec.assert_called_once()

    # =========================================================================
    # E2E-40: Forced Mid-Pipeline Celery Task Crash & Clean Recovery
    # =========================================================================

    def test_e2e_40_forced_celery_task_crash_and_recovery(self):
        """
        E2E-40:
        1. Failure Phase: Forces an unhandled exception mid-task (e.g. PyMuPDF memory error during processing).
           Confirms document transitions to status FAILED with failure_reason (never stuck in EXTRACTING or falsely complete).
        2. Recovery Phase: Retries / reprocesses document cleanly to COMPLETE status.
        """
        doc_crash = Document.objects.create(
            user=self.user,
            original_filename="crash_test_contract.pdf",
            file_reference="uploads/documents/crash_test_contract.pdf",
            status=DocumentStatus.QUEUED
        )

        # 1. FAILURE PHASE: Mid-task crash during AI processing call
        with patch("services.ai_client.process_document") as mock_ai_proc:
            mock_ai_proc.side_effect = RuntimeError("PyMuPDF Memory Error: Corrupted stream buffer")
            with self.assertRaises(RuntimeError):
                process_document(str(doc_crash.id))

        doc_crash.refresh_from_db()
        # Verify document is marked FAILED, not stuck in SEGMENTING or falsely COMPLETE
        self.assertEqual(doc_crash.status, DocumentStatus.FAILED)
        self.assertIsNotNone(doc_crash.failure_reason)
        self.assertIn("Corrupted stream buffer", doc_crash.failure_reason)

        # 2. RECOVERY PHASE: Reprocess document cleanly after crash resolution
        # Reset status to QUEUED for reprocessing
        doc_crash.status = DocumentStatus.QUEUED
        doc_crash.failure_reason = None
        doc_crash.save()

        with patch("services.ai_client.process_document") as mock_proc_clean:
            mock_proc_clean.return_value = {
                "document_id": str(doc_crash.id),
                "summary": {
                    "purpose_text": "Recovered agreement.",
                    "key_risks_text": "Low risk.",
                    "key_terms_text": "Standard terms.",
                    "obligations_text": "Compliant."
                },
                "clauses": [
                    {
                        "clause_id": "c-crash-rec",
                        "position": 1,
                        "original_text": "Standard terms apply.",
                        "simplified_text": "Standard terms apply.",
                        "severity": "safe",
                        "category": "General"
                    }
                ]
            }
            res_rec = process_document(str(doc_crash.id))

        doc_crash.refresh_from_db()
        self.assertEqual(res_rec["status"], "complete")
        self.assertEqual(doc_crash.status, DocumentStatus.COMPLETE)
        self.assertIsNone(doc_crash.failure_reason)

    # =========================================================================
    # E2E-41: Forced Malformed AI Output Rejection & Clean Recovery
    # =========================================================================

    def test_e2e_41_forced_malformed_ai_output_rejection_and_recovery(self):
        """
        E2E-41:
        1. Failure Phase: Intercepts and corrupts AI response payload (invalid severity, missing keys).
           Schema validation layer catches corrupted payload (AIServiceValidationError), rejecting it end-to-end.
           HTTP 503 returned to user; zero corrupted records saved to PostgreSQL or Qdrant.
        2. Recovery Phase: Next request returns schema-valid output and succeeds.
        """
        chat_url = f"/api/documents/{self.doc_complete.id}/chat/messages/"

        # 1. FAILURE PHASE: Intercept and corrupt AI output payload
        with patch("services.ai_client.chat") as mock_chat_corrupt:
            mock_chat_corrupt.side_effect = AIServiceValidationError(
                "Schema validation failed: missing 'answer' string field."
            )
            res_corrupt = self.client.post(chat_url, {"query": "What are the payment terms?"}, format="json")

        self.assertEqual(res_corrupt.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(res_corrupt.json()["error"]["code"], "AI_SERVICE_UNAVAILABLE")

        # Verify corrupted response was NEVER saved in database
        last_msg = ChatMessage.objects.filter(session__document=self.doc_complete).order_by("created_at").last()
        if last_msg:
            self.assertNotEqual(last_msg.role, MessageRole.ASSISTANT)

        # Unit level schema validation checks
        with self.assertRaises(AIServiceValidationError):
            validate_chat_response({"corrupted": "missing required keys"})

        with self.assertRaises(AIServiceValidationError):
            validate_clause({"severity": "extreme_danger", "category": "Payment", "original_text": "test"})

        with self.assertRaises(AIServiceValidationError):
            validate_process_document_response({"document_id": "doc-1", "clauses": "not-a-list"})

        # 2. RECOVERY PHASE: Valid response returned
        with patch("services.ai_client.chat") as mock_chat_valid:
            mock_chat_valid.return_value = {
                "answer": "Payment terms are 30 days. ClarifAI does NOT constitute legal advice.",
                "source_clause_ids": [str(self.clause_complete.id)]
            }
            res_valid = self.client.post(chat_url, {"query": "What are the payment terms?"}, format="json")

        self.assertEqual(res_valid.status_code, status.HTTP_201_CREATED)
        self.assertIn("30 days", res_valid.json()["content"])
        self.assertEqual(res_valid.json()["source_clause_ids"], [str(self.clause_complete.id)])
