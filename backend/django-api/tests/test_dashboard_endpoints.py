"""
Phase 13 Dashboard & History APIs Tests:
- GET /api/dashboard/summary returns correct aggregated counts (total_documents, in_progress_count, flagged_risk_count, completed_count, failed_count)
- Cross-user scoping test: Dashboard summary never includes another user's document statistics
- Document overall_risk computed field test
- Document list verification: Confirming GET /api/documents/ serves history list without search/filter/sort parameters per Ch. 59
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import Clause, ClauseSeverity, Document, DocumentStatus

User = get_user_model()


class DashboardEndpointsTestCase(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            email='dashusera@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='dashuserb@example.com',
            password='Password123!'
        )

        # User A Documents:
        # 1. Complete with high risk clause
        self.doc_a_high = Document.objects.create(
            user=self.user_a,
            original_filename='usera_high.pdf',
            file_reference='uploads/documents/usera_high.pdf',
            status=DocumentStatus.COMPLETE
        )
        Clause.objects.create(
            document=self.doc_a_high,
            position=1,
            original_text='High risk clause.',
            severity=ClauseSeverity.HIGH
        )

        # 2. Complete with safe clauses only
        self.doc_a_safe = Document.objects.create(
            user=self.user_a,
            original_filename='usera_safe.pdf',
            file_reference='uploads/documents/usera_safe.pdf',
            status=DocumentStatus.COMPLETE
        )
        Clause.objects.create(
            document=self.doc_a_safe,
            position=1,
            original_text='Safe clause text.',
            severity=ClauseSeverity.SAFE
        )

        # 3. In-progress document (EXTRACTING)
        self.doc_a_progress = Document.objects.create(
            user=self.user_a,
            original_filename='usera_progress.pdf',
            file_reference='uploads/documents/usera_progress.pdf',
            status=DocumentStatus.EXTRACTING
        )

        # 4. Failed document
        self.doc_a_failed = Document.objects.create(
            user=self.user_a,
            original_filename='usera_failed.pdf',
            file_reference='uploads/documents/usera_failed.pdf',
            status=DocumentStatus.FAILED,
            failure_reason='Corrupted PDF'
        )

        # User B Documents (Should be excluded from User A's dashboard):
        self.doc_b1 = Document.objects.create(
            user=self.user_b,
            original_filename='userb_doc1.pdf',
            file_reference='uploads/documents/userb_doc1.pdf',
            status=DocumentStatus.COMPLETE
        )
        Clause.objects.create(
            document=self.doc_b1,
            position=1,
            original_text='User B clause.',
            severity=ClauseSeverity.HIGH
        )

    def test_dashboard_summary_counts_success(self):
        """GET /api/dashboard/summary returns correct user-scoped counts for mixed document statuses."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('dashboard_summary')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data['total_documents'], 4)
        self.assertEqual(data['completed_count'], 2)
        self.assertEqual(data['in_progress_count'], 1)
        self.assertEqual(data['failed_count'], 1)
        self.assertEqual(data['flagged_risk_count'], 1)  # Only doc_a_high has non-Safe clause

    def test_dashboard_summary_cross_user_isolation(self):
        """GET /api/dashboard/summary for User B excludes User A's documents entirely."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('dashboard_summary')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data['total_documents'], 1)
        self.assertEqual(data['completed_count'], 1)
        self.assertEqual(data['in_progress_count'], 0)
        self.assertEqual(data['failed_count'], 0)
        self.assertEqual(data['flagged_risk_count'], 1)

    def test_document_computed_overall_risk_field(self):
        """DocumentDetailSerializer returns computed overall_risk field for completed and incomplete documents."""
        self.client.force_authenticate(user=self.user_a)

        # Check high risk doc
        res_high = self.client.get(reverse('document_detail_delete', kwargs={'pk': self.doc_a_high.id}))
        self.assertEqual(res_high.status_code, status.HTTP_200_OK)
        self.assertEqual(res_high.data['overall_risk'], 'high')

        # Check safe doc
        res_safe = self.client.get(reverse('document_detail_delete', kwargs={'pk': self.doc_a_safe.id}))
        self.assertEqual(res_safe.status_code, status.HTTP_200_OK)
        self.assertEqual(res_safe.data['overall_risk'], 'safe')

        # Check in-progress doc (should return None)
        res_prog = self.client.get(reverse('document_detail_delete', kwargs={'pk': self.doc_a_progress.id}))
        self.assertEqual(res_prog.status_code, status.HTTP_200_OK)
        self.assertIsNone(res_prog.data['overall_risk'])

    def test_document_list_serves_history_without_search_filter_sort(self):
        """GET /api/documents/ returns paginated document history without adding search/filter/sort parameters per Ch. 59."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_list_create')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 4)
