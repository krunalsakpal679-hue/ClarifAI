"""
Phase 12 Export & Report Generation Microservice / Backend Endpoint Tests:
- POST /api/documents/{id}/report (successful document PDF report generation)
- POST /api/comparisons/{id}/report (successful comparison PDF report generation)
- GET /api/reports/{id}/download (secure PDF file streaming download)
- Exactly-one-of document_id/comparison_id validation rule
- Ownership enforcement (404 Not Found for non-owners)
- Incomplete resource rejection (422 DOCUMENT_NOT_READY)
- Failure isolation (generation failure marks report FAILED without corrupting Document/Clause/Comparison DB data)
"""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comparison.models import Comparison, ComparisonCategory, ComparisonResult, ComparisonStatus
from apps.documents.models import Clause, Document, DocumentStatus, DocumentSummary
from apps.reports.models import Report, ReportStatus
from apps.reports.serializers import ReportSerializer

User = get_user_model()


class ReportEndpointsTestCase(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            email='reportusera@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='reportuserb@example.com',
            password='Password123!'
        )

        # Complete Document owned by User A
        self.doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='usera_contract.pdf',
            file_reference='uploads/documents/usera_contract.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.summary_a = DocumentSummary.objects.create(
            document=self.doc_a,
            purpose_text='Standard commercial contract summary overview.',
            obligations_text='Net 30 payment, 2-year NDA.'
        )

        self.clause_a = Clause.objects.create(
            document=self.doc_a,
            position=1,
            original_text='Payment due in 30 days.',
            simplified_text='Pay within 30 days.',
            severity='moderate',
            category='Payment'
        )

        # Incomplete Document owned by User A
        self.incomplete_doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='usera_incomplete.pdf',
            file_reference='uploads/documents/usera_incomplete.pdf',
            status=DocumentStatus.EXTRACTING
        )

        # Complete Comparison owned by User A
        self.doc_a2 = Document.objects.create(
            user=self.user_a,
            original_filename='usera_v2.pdf',
            file_reference='uploads/documents/usera_v2.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.comp_a = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a,
            target_document=self.doc_a2,
            status=ComparisonStatus.COMPLETE
        )
        self.comp_result_a = ComparisonResult.objects.create(
            comparison=self.comp_a,
            category=ComparisonCategory.CHANGED,
            difference_explanation='Payment window reduced from 30 to 15 days.',
            similarity_score=0.75
        )

    def test_document_report_generation_and_download_success(self):
        """POST /api/documents/{id}/report generates PDF and GET /api/reports/{id}/download downloads file."""
        self.client.force_authenticate(user=self.user_a)
        url_create = reverse('document_report_create', kwargs={'pk': self.doc_a.id})
        
        # 1. Generate Document Report
        res_create = self.client.post(url_create, {'language': 'en'})
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        report_id = res_create.data['id']

        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, ReportStatus.COMPLETE)
        self.assertEqual(report.document, self.doc_a)
        self.assertIsNone(report.comparison)

        # 2. Download Report PDF File
        url_download = reverse('report_download', kwargs={'pk': report_id})
        res_download = self.client.get(url_download)
        self.assertEqual(res_download.status_code, status.HTTP_200_OK)
        self.assertEqual(res_download['Content-Type'], 'application/pdf')
        self.assertIn('attachment', res_download['Content-Disposition'])

    def test_comparison_report_generation_and_download_success(self):
        """POST /api/comparisons/{id}/report generates PDF and GET /api/reports/{id}/download downloads file."""
        self.client.force_authenticate(user=self.user_a)
        url_create = reverse('comparison_report_create', kwargs={'pk': self.comp_a.id})
        
        # 1. Generate Comparison Report
        res_create = self.client.post(url_create, {'language': 'en'})
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        report_id = res_create.data['id']

        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, ReportStatus.COMPLETE)
        self.assertEqual(report.comparison, self.comp_a)
        self.assertIsNone(report.document)

        # 2. Download Report PDF File
        url_download = reverse('report_download', kwargs={'pk': report_id})
        res_download = self.client.get(url_download)
        self.assertEqual(res_download.status_code, status.HTTP_200_OK)
        self.assertEqual(res_download['Content-Type'], 'application/pdf')

    def test_exactly_one_of_document_or_comparison_validation(self):
        """Serializer validates that exactly one of (document, comparison) is set."""
        # Both set -> invalid
        serializer_both = ReportSerializer(data={
            'document': str(self.doc_a.id),
            'comparison': str(self.comp_a.id),
            'language': 'en'
        })
        self.assertFalse(serializer_both.is_valid())
        self.assertIn('non_field_errors', serializer_both.errors)

        # Neither set -> invalid
        serializer_neither = ReportSerializer(data={
            'language': 'en'
        })
        self.assertFalse(serializer_neither.is_valid())
        self.assertIn('non_field_errors', serializer_neither.errors)

    def test_ownership_enforcement_returns_404(self):
        """Non-owner attempting to generate report or download PDF receives 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        
        # Attempt to generate report on User A's document
        url_doc_report = reverse('document_report_create', kwargs={'pk': self.doc_a.id})
        res_doc = self.client.post(url_doc_report, {'language': 'en'})
        self.assertEqual(res_doc.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to generate report on User A's comparison
        url_comp_report = reverse('comparison_report_create', kwargs={'pk': self.comp_a.id})
        res_comp = self.client.post(url_comp_report, {'language': 'en'})
        self.assertEqual(res_comp.status_code, status.HTTP_404_NOT_FOUND)

        # Create a report owned by User A
        report_a = Report.objects.create(
            user=self.user_a,
            document=self.doc_a,
            status=ReportStatus.COMPLETE,
            file_reference=self.doc_a.file_reference
        )

        # Attempt to download User A's report as User B
        url_download = reverse('report_download', kwargs={'pk': report_a.id})
        res_download = self.client.get(url_download)
        self.assertEqual(res_download.status_code, status.HTTP_404_NOT_FOUND)

    def test_incomplete_resource_report_generation_returns_422(self):
        """POST /api/documents/{id}/report on incomplete document returns 422 DOCUMENT_NOT_READY."""
        self.client.force_authenticate(user=self.user_a)
        url_create = reverse('document_report_create', kwargs={'pk': self.incomplete_doc_a.id})
        
        response = self.client.post(url_create, {'language': 'en'})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['error']['code'], 'DOCUMENT_NOT_READY')

    def test_pdf_generation_failure_isolation(self):
        """PDF generation failure sets report.status = FAILED without corrupting Document/Clause DB records."""
        self.client.force_authenticate(user=self.user_a)
        url_create = reverse('document_report_create', kwargs={'pk': self.doc_a.id})

        with patch("apps.reports.views.generate_document_pdf", side_effect=RuntimeError("Simulated PDF engine crash")):
            response = self.client.post(url_create, {'language': 'en'})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Report record status should be FAILED
        report = Report.objects.filter(user=self.user_a, document=self.doc_a).last()
        self.assertIsNotNone(report)
        self.assertEqual(report.status, ReportStatus.FAILED)
        self.assertIn("Simulated PDF engine crash", report.failure_reason)

        # Underlying Document, Clause, and Summary records remain 100% intact
        self.doc_a.refresh_from_db()
        self.assertEqual(self.doc_a.status, DocumentStatus.COMPLETE)
        self.assertEqual(self.doc_a.clauses.count(), 1)
        self.assertIsNotNone(self.doc_a.summary)
