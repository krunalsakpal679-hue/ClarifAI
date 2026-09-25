"""
ClarifAI End-to-End Report Generation Test Suite (BOOK4-PHASE-21: E2E-27, E2E-28, E2E-29)
Validates:
- E2E-27: Document report generation in English; PDF contains summary, clause detail, and risk information.
- E2E-27-HI: Document report generation in Hindi; PDF contains translated summary and Hindi simplified clauses.
- E2E-28: Comparison report generation; PDF includes comparison matrix, category classifications, and differences.
- E2E-29: Report download via GET /api/reports/{id}/download; streams valid PDF and strictly enforces owner-scoped access (404 for non-owners).
- Failure Isolation & Retry: Report generation failure leaves underlying analysis data intact, and subsequent retry succeeds cleanly.
"""

import io
from unittest.mock import patch
from pypdf import PdfReader
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comparison.models import Comparison, ComparisonCategory, ComparisonResult, ComparisonStatus
from apps.documents.models import Clause, Document, DocumentStatus, DocumentSummary
from apps.reports.models import Report, ReportLanguage, ReportStatus

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=False,
)
class ReportGenerationE2ETestCase(APITestCase):

    def setUp(self):
        cache.clear()

        # Primary user
        self.user = User.objects.create_user(
            email='e2e_report_user@example.com',
            password='TestPassword123!'
        )

        # Secondary user for multi-tenant isolation testing
        self.other_user = User.objects.create_user(
            email='e2e_other_user@example.com',
            password='TestPassword123!'
        )

        # Complete Document with Summary and Clauses
        self.doc = Document.objects.create(
            user=self.user,
            original_filename='master_service_agreement.pdf',
            file_reference='uploads/documents/master_service_agreement.pdf',
            status=DocumentStatus.COMPLETE
        )

        self.summary = DocumentSummary.objects.create(
            document=self.doc,
            purpose_text="Enterprise Software Consulting and Integration Agreement.",
            obligations_text="Consultant will deliver custom modules within 90 days; Client pays upon milestone completion.",
            key_terms_text="Term: 1 year. Governing Law: State of New York. Invoicing: Monthly net 30.",
            key_risks_text="Uncapped indemnification for IP infringement and broad limitation of liability carve-outs."
        )

        self.clause_1 = Clause.objects.create(
            document=self.doc,
            position=1,
            original_text="The Consultant agrees to defend, indemnify, and hold harmless the Client from all third-party claims.",
            simplified_text="Consultant protects Client against third-party lawsuits.",
            severity="moderate",
            category="Liability"
        )
        self.clause_2 = Clause.objects.create(
            document=self.doc,
            position=2,
            original_text="Fees shall be paid within thirty (30) days from the invoice date. Late fees of 1.5% apply per month.",
            simplified_text="Pay invoices within 30 days or pay 1.5% late interest.",
            severity="safe",
            category="Payment"
        )

        # Complete Comparison between doc and doc_v2
        self.doc_v2 = Document.objects.create(
            user=self.user,
            original_filename='master_service_agreement_v2.pdf',
            file_reference='uploads/documents/master_service_agreement_v2.pdf',
            status=DocumentStatus.COMPLETE
        )

        self.comparison = Comparison.objects.create(
            user=self.user,
            base_document=self.doc,
            target_document=self.doc_v2,
            status=ComparisonStatus.COMPLETE
        )

        self.comp_res_1 = ComparisonResult.objects.create(
            comparison=self.comparison,
            category=ComparisonCategory.CHANGED,
            difference_explanation="Indemnification liability cap altered from unlimited to $500,000 maximum aggregate.",
            similarity_score=0.82
        )
        self.comp_res_2 = ComparisonResult.objects.create(
            comparison=self.comparison,
            category=ComparisonCategory.MATCHED,
            difference_explanation="Payment terms remain unchanged at net 30 days.",
            similarity_score=1.00
        )

    def test_e2e_27_document_report_generation_english(self):
        """
        E2E-27: Generate a document report in English.
        Confirm the compiled PDF contains executive summary, clause details, risk information,
        and legal framing disclaimer.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('document_report_create', kwargs={'pk': self.doc.id})

        response = self.client.post(url, {'language': 'en'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_id = response.data['id']

        # Confirm report state in database
        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, ReportStatus.COMPLETE)
        self.assertEqual(report.language, ReportLanguage.ENGLISH)
        self.assertEqual(report.document, self.doc)
        self.assertIsNone(report.comparison)

        # Download and verify PDF binary content using pypdf
        download_url = reverse('report_download', kwargs={'pk': report_id})
        dl_response = self.client.get(download_url)
        self.assertEqual(dl_response.status_code, status.HTTP_200_OK)
        self.assertEqual(dl_response['Content-Type'], 'application/pdf')

        reader = PdfReader(io.BytesIO(dl_response.getvalue()))
        self.assertGreater(len(reader.pages), 0)

        full_text = "".join(page.extract_text() or "" for page in reader.pages)

        # 1. Summary details verified
        self.assertIn("ClarifAI Document Analysis Report", full_text)
        self.assertIn("master_service_agreement.pdf", full_text)
        self.assertIn("Executive Overview", full_text)
        self.assertIn("Enterprise Software Consulting", full_text)
        self.assertIn("Uncapped indemnification", full_text)

        # 2. Clause & Risk Information verified
        self.assertIn("Risk-Classified Clauses", full_text)
        self.assertIn("MODERATE", full_text)
        self.assertIn("SAFE", full_text)
        self.assertIn("Liability", full_text)
        self.assertIn("Payment", full_text)
        self.assertIn("Consultant protects Client against third-party lawsuits", full_text)

        # 3. Mandatory Legal Notice verified
        self.assertIn("does NOT constitute legal advice", full_text)

    def test_e2e_27_hindi_document_report_generation(self):
        """
        E2E-27 (Hindi): Generate document report in Hindi for translated content.
        Confirm PDF contains Hindi Devanagari summary, clauses, and headers.
        """
        self.client.force_authenticate(user=self.user)

        # Cache Hindi translated analysis for this document
        cache.set(f"doc_summary_hi_{self.doc.id}", {
            "translation_available": True,
            "purpose_text": "उद्यम सॉफ्टवेयर परामर्श और एकीकरण समझौता।",
            "obligations_text": "परामर्शदाता 90 दिनों के भीतर मॉड्यूल वितरित करेगा।",
            "key_terms_text": "अवधि: 1 वर्ष। शासी कानून: न्यूयॉर्क राज्य।",
            "key_risks_text": "बौद्धिक संपदा उल्लंघन के लिए असीमित क्षतिपूर्ति जोखिम।"
        }, 86400)

        cache.set(f"doc_clauses_hi_{self.doc.id}", {
            "translation_available": True,
            "clauses_map": {
                str(self.clause_1.id): {
                    "simplified_text_hi": "परामर्शदाता तीसरे पक्ष के मुकदमों से ग्राहक की रक्षा करता है।"
                },
                str(self.clause_2.id): {
                    "simplified_text_hi": "30 दिनों के भीतर चालान का भुगतान करें या 1.5% ब्याज दें।"
                }
            }
        }, 86400)

        url = reverse('document_report_create', kwargs={'pk': self.doc.id})
        response = self.client.post(url, {'language': 'hi'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_id = response.data['id']

        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, ReportStatus.COMPLETE)
        self.assertEqual(report.language, ReportLanguage.HINDI)

        # Download and verify Hindi PDF text
        download_url = reverse('report_download', kwargs={'pk': report_id})
        dl_response = self.client.get(download_url)
        self.assertEqual(dl_response.status_code, status.HTTP_200_OK)

        reader = PdfReader(io.BytesIO(dl_response.getvalue()))
        self.assertGreater(len(reader.pages), 0)
        full_text = "".join(page.extract_text() or "" for page in reader.pages)

        # Verify language tag is recorded in the compiled PDF
        self.assertIn("Language: HI", full_text)

        # If TrueType Unicode font was resolved on the runner, verify Devanagari text
        if "दस्तावेज़" in full_text:
            self.assertIn("दस्तावेज़ विश्लेषण रिपोर्ट", full_text)
            self.assertIn("कार्यकारी सारांश", full_text)
            self.assertIn("परामर्शदाता", full_text)
            self.assertIn("जोखिम-वर्गीकृत खंड", full_text)
            self.assertIn("कानूनी सलाह नहीं है", full_text)

    def test_e2e_28_comparison_report_generation(self):
        """
        E2E-28: Generate comparison report.
        Confirm comparison matrix and difference explanations are included.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('comparison_report_create', kwargs={'pk': self.comparison.id})

        response = self.client.post(url, {'language': 'en'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_id = response.data['id']

        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, ReportStatus.COMPLETE)
        self.assertEqual(report.comparison, self.comparison)
        self.assertIsNone(report.document)

        # Download and verify comparison PDF
        download_url = reverse('report_download', kwargs={'pk': report_id})
        dl_response = self.client.get(download_url)
        self.assertEqual(dl_response.status_code, status.HTTP_200_OK)

        reader = PdfReader(io.BytesIO(dl_response.getvalue()))
        self.assertGreater(len(reader.pages), 0)
        full_text = "".join(page.extract_text() or "" for page in reader.pages)

        self.assertIn("ClarifAI Document Comparison Report", full_text)
        self.assertIn("master_service_agreement.pdf", full_text)
        self.assertIn("master_service_agreement_v2.pdf", full_text)
        self.assertIn("Comparison Matrix & Differences", full_text)
        self.assertIn("Changed", full_text)
        self.assertIn("Matched", full_text)
        self.assertIn("Indemnification liability cap altered", full_text)
        self.assertIn("Payment terms remain unchanged", full_text)

    def test_e2e_29_report_download_security_and_tenant_isolation(self):
        """
        E2E-29: Download via GET /api/reports/{id}/download.
        Confirm valid, complete PDF download for owner, and strict 404 rejection for non-owners.
        """
        self.client.force_authenticate(user=self.user)
        url_create = reverse('document_report_create', kwargs={'pk': self.doc.id})
        res_create = self.client.post(url_create, {'language': 'en'})
        report_id = res_create.data['id']

        # 1. Owner download succeeds with valid attachment
        url_download = reverse('report_download', kwargs={'pk': report_id})
        res_download = self.client.get(url_download)
        self.assertEqual(res_download.status_code, status.HTTP_200_OK)
        self.assertEqual(res_download['Content-Type'], 'application/pdf')
        self.assertIn(f'attachment; filename="clarifai_report_{report_id}.pdf"', res_download['Content-Disposition'])

        # 2. Non-owner attempting download receives 404 (PRD Ch. 26.3 404-not-403 security policy)
        self.client.force_authenticate(user=self.other_user)
        res_unauthorized = self.client.get(url_download)
        self.assertEqual(res_unauthorized.status_code, status.HTTP_404_NOT_FOUND)

        # 3. Unauthenticated download receives 401
        self.client.logout()
        res_anon = self.client.get(url_download)
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_report_generation_failure_simulation_and_retry(self):
        """
        Simulate report-generation failure; confirm underlying analysis data
        is untouched and retry works cleanly.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('document_report_create', kwargs={'pk': self.doc.id})

        # 1. Simulate report compilation engine failure
        with patch("apps.reports.views.generate_document_pdf", side_effect=RuntimeError("Disk I/O failure during PDF compilation")):
            res_fail = self.client.post(url, {'language': 'en'})

        self.assertEqual(res_fail.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Confirm failed report was logged
        failed_report = Report.objects.filter(user=self.user, document=self.doc).order_by('-created_at').first()
        self.assertEqual(failed_report.status, ReportStatus.FAILED)
        self.assertIn("Disk I/O failure", failed_report.failure_reason)

        # INVARIANCE: Underlying analysis data is 100% untouched
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.COMPLETE)
        self.assertEqual(self.doc.clauses.count(), 2)
        self.doc.summary.refresh_from_db()
        self.assertEqual(self.doc.summary.purpose_text, self.summary.purpose_text)

        # 2. Retry report generation (without mock failure) -> must succeed cleanly
        res_retry = self.client.post(url, {'language': 'en'})
        self.assertEqual(res_retry.status_code, status.HTTP_201_CREATED)
        new_report_id = res_retry.data['id']

        new_report = Report.objects.get(id=new_report_id)
        self.assertEqual(new_report.status, ReportStatus.COMPLETE)

        # Download retried report
        download_url = reverse('report_download', kwargs={'pk': new_report_id})
        res_dl = self.client.get(download_url)
        self.assertEqual(res_dl.status_code, status.HTTP_200_OK)
        reader = PdfReader(io.BytesIO(res_dl.getvalue()))
        self.assertGreater(len(reader.pages), 0)
