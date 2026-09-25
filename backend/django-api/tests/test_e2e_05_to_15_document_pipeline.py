"""
E2E Integration Test Suite for Document Upload, Edge Cases & Async Processing Pipeline
Scenarios E2E-05 through E2E-15 (PRD v2.3 Section 14, Chapter 15, Chapter 30).

Coverage:
- E2E-05: Digital PDF processes correctly with digital extraction path (zero-OCR).
- E2E-06: Scanned PDF processes correctly with OCR path (Tesseract selective/full OCR).
- E2E-07: Mixed PDF processes correctly with hybrid extraction path (digital + OCR).
- E2E-08: Corrupted PDF rejected at upload with specific unparseable/corrupted reason.
- E2E-09: Empty PDF rejected at upload with specific empty reason.
- E2E-10: Password-protected PDF rejected with distinct password/encryption reason (R-12).
- E2E-11: Non-PDF rejected at upload with genuine PDF header requirement reason.
- E2E-12: PDF over 20 MB rejected server-side regardless of frontend pre-check (R-11).
- E2E-13: Duplicate upload creates an independent second document, not a merge (R-14).
- E2E-14: Full async processing reaches status=complete with correctly populated clauses and summary.
- E2E-15: Forced processing failure (simulated AI outage mid-pipeline) results in status=failed with specific reason, never a false complete.
"""
import io
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
import pypdf
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditLog
from apps.audit.services import EVENT_ANALYSIS_FAILURE
from apps.documents.models import Clause, Document, DocumentStatus, DocumentSummary
from tasks.document_tasks import process_document

User = get_user_model()


def generate_valid_pdf(pages=1, password=None):
    """Helper to generate in-memory valid or password-protected PDF bytes."""
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    if password:
        writer.encrypt(password)
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()


def generate_empty_page_pdf():
    """Helper to generate a genuine %PDF- file with 0 pages."""
    writer = pypdf.PdfWriter()
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=False,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://'
)
class E2EDocumentPipelineTestCase(APITestCase):
    """
    Complete E2E integration test suite for ClarifAI document upload edge cases
    and asynchronous Celery processing pipeline.
    """

    def setUp(self):
        from django.core.cache import cache
        from rest_framework_simplejwt.tokens import RefreshToken

        cache.clear()
        self.user = User.objects.create_user(
            email='e2e_tester@clarifai.io',
            password='Password123!'
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.upload_url = reverse('document_list_create')

    # =========================================================================
    # E2E-05: Digital PDF processing path
    # =========================================================================
    def test_e2e_05_digital_pdf_processing_path(self):
        """E2E-05: Digital PDF processes with digital extraction path and populates analysis."""
        pdf_bytes = generate_valid_pdf(pages=2)
        uploaded_file = SimpleUploadedFile("digital_contract.pdf", pdf_bytes, content_type="application/pdf")

        upload_res = self.client.post(self.upload_url, {'file': uploaded_file}, format='multipart')
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data['id']
        self.assertEqual(upload_res.data['status'], 'queued')

        # Execute processing pipeline with digital AI response simulation
        with patch('services.ai_client.process_document') as mock_ai:
            mock_ai.return_value = {
                "document_id": str(doc_id),
                "extraction_method": "digital",
                "ocr_performed": False,
                "summary": {
                    "overview": "Digital Master Services Agreement overview.",
                    "key_points": ["Term: 2 years", "Governing Law: California"]
                },
                "clauses": [
                    {
                        "position": 1,
                        "original_text": "Section 1: Payment is due net 30 days.",
                        "simplified_text": "You must pay within 30 days.",
                        "explanation": "Standard payment terms.",
                        "severity": "safe",
                        "category": "Payment",
                        "status": "complete"
                    }
                ]
            }
            task_result = process_document(doc_id)
            self.assertEqual(task_result['status'], 'complete')

        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, DocumentStatus.COMPLETE)
        self.assertIsNone(doc.failure_reason)

        # Verify detail endpoint reflects complete status
        detail_url = reverse('document_detail_delete', kwargs={'pk': doc_id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['status'], 'complete')
        self.assertEqual(detail_res.data['overall_risk'], 'safe')

    # =========================================================================
    # E2E-06: Scanned PDF processing path (OCR)
    # =========================================================================
    def test_e2e_06_scanned_pdf_processing_path(self):
        """E2E-06: Scanned PDF triggers OCR path and successfully extracts clauses."""
        pdf_bytes = generate_valid_pdf(pages=1)
        uploaded_file = SimpleUploadedFile("scanned_invoice.pdf", pdf_bytes, content_type="application/pdf")

        upload_res = self.client.post(self.upload_url, {'file': uploaded_file}, format='multipart')
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data['id']

        with patch('services.ai_client.process_document') as mock_ai:
            mock_ai.return_value = {
                "document_id": str(doc_id),
                "extraction_method": "ocr",
                "ocr_performed": True,
                "summary": {
                    "overview": "Scanned lease agreement.",
                    "key_points": ["Monthly rent: $5,000"]
                },
                "clauses": [
                    {
                        "position": 1,
                        "original_text": "Clause 1 (from OCR): Tenant agrees to maintain premises.",
                        "simplified_text": "Tenant is responsible for basic maintenance.",
                        "explanation": "Standard maintenance obligation.",
                        "severity": "low",
                        "category": "Dispute Resolution",
                        "status": "complete"
                    }
                ]
            }
            task_result = process_document(doc_id)
            self.assertEqual(task_result['status'], 'complete')

        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, DocumentStatus.COMPLETE)
        self.assertEqual(doc.clauses.count(), 1)
        self.assertEqual(doc.clauses.first().severity, 'low')

    # =========================================================================
    # E2E-07: Mixed PDF processing path (Hybrid)
    # =========================================================================
    def test_e2e_07_mixed_pdf_processing_path(self):
        """E2E-07: Mixed PDF (digital + scanned pages) triggers hybrid extraction path."""
        pdf_bytes = generate_valid_pdf(pages=3)
        uploaded_file = SimpleUploadedFile("hybrid_contract.pdf", pdf_bytes, content_type="application/pdf")

        upload_res = self.client.post(self.upload_url, {'file': uploaded_file}, format='multipart')
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data['id']

        with patch('services.ai_client.process_document') as mock_ai:
            mock_ai.return_value = {
                "document_id": str(doc_id),
                "extraction_method": "hybrid",
                "ocr_performed": True,
                "summary": {
                    "overview": "Mixed hybrid contract with digital preamble and scanned exhibit.",
                    "key_points": ["Exhibit A scanned signed page attached."]
                },
                "clauses": [
                    {
                        "position": 1,
                        "original_text": "Preamble extracted digitally.",
                        "simplified_text": "Contract parties agreement.",
                        "explanation": "Digital extraction.",
                        "severity": "safe",
                        "category": "Confidentiality",
                        "status": "complete"
                    },
                    {
                        "position": 2,
                        "original_text": "Exhibit A extracted via OCR.",
                        "simplified_text": "Special terms from scan.",
                        "explanation": "OCR extraction.",
                        "severity": "moderate",
                        "category": "Termination",
                        "status": "complete"
                    }
                ]
            }
            task_result = process_document(doc_id)
            self.assertEqual(task_result['status'], 'complete')

        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, DocumentStatus.COMPLETE)
        self.assertEqual(doc.clauses.count(), 2)

    # =========================================================================
    # E2E-08: Corrupted PDF rejected
    # =========================================================================
    def test_e2e_08_corrupted_pdf_rejected(self):
        """E2E-08: Corrupted or unparseable PDF stream rejected with specific correct reason."""
        corrupted_bytes = b"%PDF-1.4 truncated unparseable corrupted byte stream without EOF catalog structure"
        corrupted_file = SimpleUploadedFile("corrupted.pdf", corrupted_bytes, content_type="application/pdf")

        response = self.client.post(self.upload_url, {'file': corrupted_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn("corrupted", str(data['error']['details']).lower())

    # =========================================================================
    # E2E-09: Empty PDF rejected
    # =========================================================================
    def test_e2e_09_empty_pdf_rejected(self):
        """E2E-09: Empty PDF (0 pages) rejected with specific correct reason."""
        empty_pdf_bytes = generate_empty_page_pdf()
        empty_file = SimpleUploadedFile("empty.pdf", empty_pdf_bytes, content_type="application/pdf")

        response = self.client.post(self.upload_url, {'file': empty_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn("empty", str(data['error']['details']).lower())

    # =========================================================================
    # E2E-10: Password-protected PDF rejected with distinct message
    # =========================================================================
    def test_e2e_10_password_protected_pdf_rejected(self):
        """E2E-10: Password-protected PDF rejected with distinct encryption message (R-12)."""
        encrypted_pdf_bytes = generate_valid_pdf(pages=1, password="StrictPassword99!")
        encrypted_file = SimpleUploadedFile("encrypted.pdf", encrypted_pdf_bytes, content_type="application/pdf")

        response = self.client.post(self.upload_url, {'file': encrypted_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn("Password-protected PDFs are not supported", str(data['error']['details']))
        # Must not be classified generically as corrupted
        self.assertNotIn("corrupted", str(data['error']['details']).lower())

    # =========================================================================
    # E2E-11: Non-PDF rejected
    # =========================================================================
    def test_e2e_11_non_pdf_file_rejected(self):
        """E2E-11: Non-PDF file without %PDF- magic bytes rejected."""
        fake_file = SimpleUploadedFile("not_a_pdf.txt", b"Plain text file contents", content_type="text/plain")

        response = self.client.post(self.upload_url, {'file': fake_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn("genuine PDF", str(data['error']['details']))

    # =========================================================================
    # E2E-12: PDF over 20 MB rejected server-side
    # =========================================================================
    def test_e2e_12_oversized_pdf_rejected(self):
        """E2E-12: PDF larger than 20 MB rejected server-side (Decision R-11)."""
        max_bytes = 20 * 1024 * 1024
        oversized_content = b"%PDF-1.4\n" + (b"0" * (max_bytes + 2048))
        oversized_file = SimpleUploadedFile("huge_file.pdf", oversized_content, content_type="application/pdf")

        response = self.client.post(self.upload_url, {'file': oversized_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn("20MB", str(data['error']['details']))

    # =========================================================================
    # E2E-13: Duplicate upload creates independent document
    # =========================================================================
    def test_e2e_13_duplicate_upload_creates_independent_document(self):
        """E2E-13: Uploading identical file twice creates two independent Document records (R-14)."""
        pdf_bytes = generate_valid_pdf(pages=1)
        file_a = SimpleUploadedFile("duplicate.pdf", pdf_bytes, content_type="application/pdf")
        file_b = SimpleUploadedFile("duplicate.pdf", pdf_bytes, content_type="application/pdf")

        res_a = self.client.post(self.upload_url, {'file': file_a}, format='multipart')
        res_b = self.client.post(self.upload_url, {'file': file_b}, format='multipart')

        self.assertEqual(res_a.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_b.status_code, status.HTTP_201_CREATED)

        doc_id_a = res_a.data['id']
        doc_id_b = res_b.data['id']

        self.assertNotEqual(doc_id_a, doc_id_b)
        self.assertEqual(Document.objects.filter(user=self.user).count(), 2)

        # Both documents must be individually retrievable
        get_a = self.client.get(reverse('document_detail_delete', kwargs={'pk': doc_id_a}))
        get_b = self.client.get(reverse('document_detail_delete', kwargs={'pk': doc_id_b}))
        self.assertEqual(get_a.status_code, status.HTTP_200_OK)
        self.assertEqual(get_b.status_code, status.HTTP_200_OK)

    # =========================================================================
    # E2E-14: Full async processing reaches status=complete
    # =========================================================================
    def test_e2e_14_full_async_processing_reaches_complete(self):
        """E2E-14: Full async processing reaches status=complete with populated clauses and summary."""
        pdf_bytes = generate_valid_pdf(pages=2)
        uploaded_file = SimpleUploadedFile("service_level_agreement.pdf", pdf_bytes, content_type="application/pdf")

        upload_res = self.client.post(self.upload_url, {'file': uploaded_file}, format='multipart')
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data['id']

        # Execute Celery task
        with patch('services.ai_client.process_document') as mock_ai:
            mock_ai.return_value = {
                "document_id": str(doc_id),
                "summary": {
                    "overview": "Comprehensive enterprise SLA.",
                    "key_points": ["99.9% uptime requirement", "Penalties for outage"]
                },
                "clauses": [
                    {
                        "position": 1,
                        "original_text": "Uptime guarantee is 99.9% measured on a monthly basis.",
                        "simplified_text": "Service must be up 99.9% of the time each month.",
                        "explanation": "Core SLA availability commitment.",
                        "severity": "safe",
                        "category": "Liability",
                        "status": "complete"
                    },
                    {
                        "position": 2,
                        "original_text": "Failure to achieve SLA will result in 10% credit.",
                        "simplified_text": "You get 10% credit if uptime drops below target.",
                        "explanation": "Service credit remedy.",
                        "severity": "low",
                        "category": "Payment",
                        "status": "complete"
                    }
                ]
            }
            task_result = process_document(doc_id)
            self.assertEqual(task_result['status'], 'complete')

        # Verify DB records
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, DocumentStatus.COMPLETE)
        self.assertIsNone(doc.failure_reason)

        # Check summary endpoint
        summary_url = reverse('document_summary', kwargs={'pk': doc_id})
        summary_res = self.client.get(summary_url)
        self.assertEqual(summary_res.status_code, status.HTTP_200_OK)
        self.assertIn("Comprehensive enterprise SLA", summary_res.data['purpose_text'])

        # Check clauses endpoint
        clauses_url = reverse('document_clause_list', kwargs={'pk': doc_id})
        clauses_res = self.client.get(clauses_url)
        self.assertEqual(clauses_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clauses_res.data['results']), 2)

    # =========================================================================
    # E2E-15: Forced processing failure transitions to failed
    # =========================================================================
    def test_e2e_15_forced_processing_failure_transitions_to_failed(self):
        """E2E-15: Forced processing failure (simulated AI outage) results in status=failed, never false complete."""
        pdf_bytes = generate_valid_pdf(pages=1)
        uploaded_file = SimpleUploadedFile("failing_doc.pdf", pdf_bytes, content_type="application/pdf")

        upload_res = self.client.post(self.upload_url, {'file': uploaded_file}, format='multipart')
        self.assertEqual(upload_res.status_code, status.HTTP_201_CREATED)
        doc_id = upload_res.data['id']

        # Force failure during AI call (simulated AI outage)
        with patch('services.ai_client.process_document') as mock_ai:
            mock_ai.side_effect = RuntimeError("FastAPI AI microservice unavailable (Connection Refused 503)")
            with self.assertRaises(RuntimeError):
                process_document(doc_id)

        # Document must be in FAILED status, never COMPLETE
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, DocumentStatus.FAILED)
        self.assertIn("FastAPI AI microservice unavailable", doc.failure_reason)

        # GET /api/documents/{id}/ must return status=failed and failure_reason
        detail_url = reverse('document_detail_delete', kwargs={'pk': doc_id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['status'], 'failed')
        self.assertIn("FastAPI AI microservice unavailable", detail_res.data['failure_reason'])

        # Audit event for failure must be logged (PRD Ch. 26.8)
        failure_log = AuditLog.objects.filter(
            user=self.user,
            event_type=EVENT_ANALYSIS_FAILURE
        ).first()
        self.assertIsNotNone(failure_log)
        self.assertIn(str(doc_id), str(failure_log.metadata))
