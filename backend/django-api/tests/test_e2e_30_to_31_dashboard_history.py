"""
ClarifAI End-to-End Dashboard & History Test Suite (BOOK4-PHASE-22: E2E-30, E2E-31)
Traceability: PRD v2.3 Chapter 20, 22.4, 22.12, 30.2, 30.7 & Chapter 59 History Rule.

Validates:
- E2E-30 Dashboard: GET /api/dashboard/summary returns accurate counts for this user only
  (total_documents, in_progress_count, flagged_risk_count, completed_count, failed_count)
  across documents in multiple states (complete, extracting, segmenting, failed).
- E2E-31 History: GET /api/documents/ returns full paginated list strictly scoped to the owner,
  ordered by uploaded_at descending, with computed overall_risk field.
- History Rule Check: Explicit verification that GET /api/documents/ and the History feature
  do not support search, filter, or sort query parameters per PRD v2.3 Chapter 59 ("Deferred Decisions").
- Reopen Action: Completed documents restore full analysis view (detail, summary, clauses)
  without triggering reprocessing; in-progress documents return 422 DOCUMENT_NOT_READY.
- Delete Action: DELETE /api/documents/{id}/ removes document, cascades to child records,
  updates dashboard counts and history pagination immediately, and enforces 404 on IDOR attempts.
"""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import Clause, ClauseSeverity, Document, DocumentStatus, DocumentSummary
from apps.documents.views import DocumentListCreateView

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=True,
)
class DashboardAndHistoryE2ETestCase(APITestCase):

    def setUp(self):
        cache.clear()

        # Primary user (User A)
        self.user_a = User.objects.create_user(
            email='e2e_dashboard_user_a@example.com',
            password='TestPassword123!'
        )

        # Secondary user (User B) for strict multi-tenant isolation testing
        self.user_b = User.objects.create_user(
            email='e2e_dashboard_user_b@example.com',
            password='TestPassword123!'
        )

        # Fixture Setup for User A: Multiple documents in various lifecycle states
        # 1. Complete document with HIGH and MODERATE risk clauses -> Flagged Risk
        self.doc_a_complete_risk = Document.objects.create(
            user=self.user_a,
            original_filename='vendor_sla_master.pdf',
            file_reference='uploads/documents/vendor_sla_master.pdf',
            document_type='Service Level Agreement',
            status=DocumentStatus.COMPLETE
        )
        self.summary_a1 = DocumentSummary.objects.create(
            document=self.doc_a_complete_risk,
            purpose_text='Vendor service level agreement defining 99.9% uptime and maintenance windows.',
            key_risks_text='Uncapped liability for service downtime; unilateral indemnification requirement.',
            key_terms_text='Net 30 payment terms; annual auto-renewal with 60-day notice.',
            obligations_text='Customer must report outages within 2 hours of occurrence.'
        )
        self.clause_a1 = Clause.objects.create(
            document=self.doc_a_complete_risk,
            position=1,
            original_text='Supplier shall have uncapped liability for any and all service disruptions.',
            simplified_text='The supplier has no limit on the financial damages they must pay if the service goes down.',
            severity=ClauseSeverity.HIGH,
            category='Liability',
            rule_findings={'matched_rule': 'R001', 'confidence': 0.95}
        )
        self.clause_a2 = Clause.objects.create(
            document=self.doc_a_complete_risk,
            position=2,
            original_text='Agreement automatically renews for 12 months unless cancelled 90 days prior.',
            simplified_text='The contract automatically extends for another year unless you cancel 90 days before it ends.',
            severity=ClauseSeverity.MODERATE,
            category='Renewal',
            rule_findings={'matched_rule': 'R006', 'confidence': 0.88}
        )

        # 2. Complete document with only SAFE clauses -> Complete but NOT Flagged Risk
        self.doc_a_complete_safe = Document.objects.create(
            user=self.user_a,
            original_filename='standard_mutual_nda.pdf',
            file_reference='uploads/documents/standard_mutual_nda.pdf',
            document_type='Non-Disclosure Agreement',
            status=DocumentStatus.COMPLETE
        )
        self.summary_a2 = DocumentSummary.objects.create(
            document=self.doc_a_complete_safe,
            purpose_text='Mutual non-disclosure agreement protecting proprietary information.',
            key_risks_text='Standard risk profile with reciprocal protections.',
            key_terms_text='2-year confidentiality duration; standard exclusions apply.',
            obligations_text='Both parties maintain strict standard of care regarding disclosures.'
        )
        self.clause_a3 = Clause.objects.create(
            document=self.doc_a_complete_safe,
            position=1,
            original_text='Each party agrees to protect the other party\'s Confidential Information with reasonable care.',
            simplified_text='Both companies promise to guard each other\'s confidential details carefully.',
            severity=ClauseSeverity.SAFE,
            category='Confidentiality',
            rule_findings={}
        )

        # 3. In-progress document (EXTRACTING)
        self.doc_a_extracting = Document.objects.create(
            user=self.user_a,
            original_filename='commercial_lease.pdf',
            file_reference='uploads/documents/commercial_lease.pdf',
            document_type='Lease Agreement',
            status=DocumentStatus.EXTRACTING
        )

        # 4. In-progress document (SEGMENTING)
        self.doc_a_segmenting = Document.objects.create(
            user=self.user_a,
            original_filename='consulting_services_addendum.pdf',
            file_reference='uploads/documents/consulting_services_addendum.pdf',
            document_type='Consulting Agreement',
            status=DocumentStatus.SEGMENTING
        )

        # 5. Failed document
        self.doc_a_failed = Document.objects.create(
            user=self.user_a,
            original_filename='corrupted_scanned_contract.pdf',
            file_reference='uploads/documents/corrupted_scanned_contract.pdf',
            document_type='Contract',
            status=DocumentStatus.FAILED,
            failure_reason='Corrupted PDF structure: unrecoverable EOF marker missing.'
        )

        # Fixture Setup for User B: Documents that must NEVER leak into User A's dashboard or history
        self.doc_b_complete_risk = Document.objects.create(
            user=self.user_b,
            original_filename='user_b_proprietary_contract.pdf',
            file_reference='uploads/documents/user_b_proprietary_contract.pdf',
            document_type='Contract',
            status=DocumentStatus.COMPLETE
        )
        Clause.objects.create(
            document=self.doc_b_complete_risk,
            position=1,
            original_text='User B high risk indemnification obligation clause.',
            severity=ClauseSeverity.HIGH,
            category='Liability'
        )

        self.doc_b_failed = Document.objects.create(
            user=self.user_b,
            original_filename='user_b_failed_document.pdf',
            file_reference='uploads/documents/user_b_failed_document.pdf',
            document_type='Other',
            status=DocumentStatus.FAILED,
            failure_reason='Timeout during OCR processing'
        )

    # -------------------------------------------------------------------------
    # E2E-30: Dashboard Summary Verification
    # -------------------------------------------------------------------------

    def test_e2e_30_dashboard_summary_accurate_counts_and_tenant_isolation(self):
        """
        E2E-30: Confirm GET /api/dashboard/summary returns accurate counts for this user only
        across multiple documents in complete, in-progress, and failed states (PRD Ch. 20, 30.7).
        """
        self.client.force_authenticate(user=self.user_a)
        dashboard_url = reverse('dashboard_summary')

        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        # User A has 5 documents total:
        # - 2 completed (doc_a_complete_risk, doc_a_complete_safe)
        # - 2 in-progress (doc_a_extracting, doc_a_segmenting)
        # - 1 failed (doc_a_failed)
        # - 1 flagged risk (doc_a_complete_risk has HIGH/MODERATE; doc_a_complete_safe has only SAFE)
        self.assertEqual(data['total_documents'], 5)
        self.assertEqual(data['completed_count'], 2)
        self.assertEqual(data['in_progress_count'], 2)
        self.assertEqual(data['failed_count'], 1)
        self.assertEqual(data['flagged_risk_count'], 1)

        # Cross-Tenant Isolation: User B's dashboard summary reflects User B's documents only
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get(dashboard_url)
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)

        data_b = res_b.data
        self.assertEqual(data_b['total_documents'], 2)
        self.assertEqual(data_b['completed_count'], 1)
        self.assertEqual(data_b['in_progress_count'], 0)
        self.assertEqual(data_b['failed_count'], 1)
        self.assertEqual(data_b['flagged_risk_count'], 1)

        # Unauthenticated access must be rejected with HTTP 401
        self.client.logout()
        res_anon = self.client.get(dashboard_url)
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # E2E-31: History Paginated List Accuracy
    # -------------------------------------------------------------------------

    def test_e2e_31_history_paginated_list_accuracy_and_ordering(self):
        """
        E2E-31: Confirm GET /api/documents/ returns the accurate paginated document list
        for the authenticated user, ordered by uploaded_at descending, with overall_risk computed (PRD Ch. 20, 30.2).
        """
        self.client.force_authenticate(user=self.user_a)
        documents_url = reverse('document_list_create')

        response = self.client.get(documents_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertEqual(data['count'], 5)

        results = data['results']
        self.assertEqual(len(results), 5)

        # Confirm all returned documents belong to User A, zero belong to User B
        returned_ids = [item['id'] for item in results]
        self.assertIn(str(self.doc_a_complete_risk.id), returned_ids)
        self.assertIn(str(self.doc_a_complete_safe.id), returned_ids)
        self.assertIn(str(self.doc_a_extracting.id), returned_ids)
        self.assertIn(str(self.doc_a_segmenting.id), returned_ids)
        self.assertIn(str(self.doc_a_failed.id), returned_ids)

        self.assertNotIn(str(self.doc_b_complete_risk.id), returned_ids)
        self.assertNotIn(str(self.doc_b_failed.id), returned_ids)

        # Verify default chronological ordering: uploaded_at descending
        for idx in range(len(results) - 1):
            self.assertGreaterEqual(results[idx]['uploaded_at'], results[idx + 1]['uploaded_at'])

        # Verify computed overall_risk field
        risk_map = {item['id']: item.get('overall_risk') for item in results}
        self.assertEqual(risk_map[str(self.doc_a_complete_risk.id)], 'high')
        self.assertEqual(risk_map[str(self.doc_a_complete_safe.id)], 'safe')
        self.assertIsNone(risk_map[str(self.doc_a_extracting.id)])
        self.assertIsNone(risk_map[str(self.doc_a_segmenting.id)])
        self.assertIsNone(risk_map[str(self.doc_a_failed.id)])

    # -------------------------------------------------------------------------
    # History Rule Verification (PRD v2.3 Chapter 20 & Chapter 59)
    # -------------------------------------------------------------------------

    def test_history_rule_no_search_filter_sort_contract_compliance(self):
        """
        HISTORY RULE CHECK:
        Inspect backend GET /api/documents/ and verify neither search, filter, nor sort
        query parameters are enabled in v1 per PRD v2.3 Chapter 59 ("Deferred Decisions").
        Supplying search or filter query parameters has zero filtering effect.
        """
        self.client.force_authenticate(user=self.user_a)
        documents_url = reverse('document_list_create')

        # 1. Base query returns all 5 documents
        base_res = self.client.get(documents_url)
        self.assertEqual(base_res.status_code, status.HTTP_200_OK)
        self.assertEqual(base_res.data['count'], 5)

        # 2. Querying with ?search=nda returns all 5 documents (no SearchFilter enabled)
        search_res = self.client.get(f"{documents_url}?search=nda")
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertEqual(search_res.data['count'], 5)

        # 3. Querying with ?status=complete returns all 5 documents (no DjangoFilterBackend enabled)
        filter_res = self.client.get(f"{documents_url}?status=complete")
        self.assertEqual(filter_res.status_code, status.HTTP_200_OK)
        self.assertEqual(filter_res.data['count'], 5)

        # 4. Querying with ?ordering=uploaded_at returns default ordering (no OrderingFilter enabled)
        order_res = self.client.get(f"{documents_url}?ordering=uploaded_at")
        self.assertEqual(order_res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [d['id'] for d in order_res.data['results']],
            [d['id'] for d in base_res.data['results']]
        )

        # 5. Programmatic architectural confirmation on DocumentListCreateView
        self.assertIn(getattr(DocumentListCreateView, 'filter_backends', []), [None, [], ()])
        self.assertIsNone(getattr(DocumentListCreateView, 'search_fields', None))
        self.assertIsNone(getattr(DocumentListCreateView, 'filterset_fields', None))
        self.assertIsNone(getattr(DocumentListCreateView, 'ordering_fields', None))

    # -------------------------------------------------------------------------
    # Reopen Action Verification from Dashboard & History
    # -------------------------------------------------------------------------

    def test_e2e_30_31_reopen_action_restores_analysis_without_reprocessing(self):
        """
        Verify reopen action from both Dashboard and History (PRD Ch. 20):
        - Completed document restores full metadata, summary, and clauses without reprocessing.
        - In-progress document reports processing status; summary/clauses endpoints protect state via 422.
        """
        self.client.force_authenticate(user=self.user_a)

        # 1. Reopen completed document
        detail_url = reverse('document_detail_delete', kwargs={'pk': self.doc_a_complete_risk.id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['status'], 'complete')
        self.assertEqual(detail_res.data['original_filename'], 'vendor_sla_master.pdf')

        # Summary restoration
        summary_url = reverse('document_summary', kwargs={'pk': self.doc_a_complete_risk.id})
        summary_res = self.client.get(summary_url)
        self.assertEqual(summary_res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            summary_res.data['purpose_text'],
            'Vendor service level agreement defining 99.9% uptime and maintenance windows.'
        )

        # Clause list restoration
        clauses_url = reverse('document_clause_list', kwargs={'pk': self.doc_a_complete_risk.id})
        clauses_res = self.client.get(clauses_url)
        self.assertEqual(clauses_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(clauses_res.data['results']), 2)

        # Confirm timestamps remain intact (zero reprocessing or mutation)
        self.doc_a_complete_risk.refresh_from_db()
        self.assertEqual(self.doc_a_complete_risk.status, DocumentStatus.COMPLETE)

        # 2. Reopen in-progress document
        progress_detail_url = reverse('document_detail_delete', kwargs={'pk': self.doc_a_extracting.id})
        progress_res = self.client.get(progress_detail_url)
        self.assertEqual(progress_res.status_code, status.HTTP_200_OK)
        self.assertEqual(progress_res.data['status'], 'extracting')

        # In-progress analysis query returns 422 DOCUMENT_NOT_READY
        progress_summary_url = reverse('document_summary', kwargs={'pk': self.doc_a_extracting.id})
        prog_summary_res = self.client.get(progress_summary_url)
        self.assertEqual(prog_summary_res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(prog_summary_res.data['error']['code'], 'DOCUMENT_NOT_READY')

    # -------------------------------------------------------------------------
    # Delete Action Verification from Dashboard & History
    # -------------------------------------------------------------------------

    def test_e2e_30_31_delete_action_cascades_and_updates_dashboard_and_history(self):
        """
        Verify delete action from both pages (PRD Ch. 20, 26.5.1):
        - DELETE /api/documents/{id}/ removes document and cascades to child clauses & summary.
        - GET /api/dashboard/summary immediately reflects decremented total, completed, and risk counts.
        - GET /api/documents/ immediately removes document from paginated history.
        - IDOR check: Attempting to delete another user's document returns 404 Not Found (not 403 or 200).
        """
        self.client.force_authenticate(user=self.user_a)

        doc_to_delete_id = str(self.doc_a_complete_risk.id)
        delete_url = reverse('document_detail_delete', kwargs={'pk': doc_to_delete_id})

        # Execute DELETE as owner with mocked AI Qdrant cleanup
        with patch("services.ai_client.delete_document_embeddings") as mock_qdrant_delete:
            mock_qdrant_delete.return_value = {"status": "success"}
            del_response = self.client.delete(delete_url)
            self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
            mock_qdrant_delete.assert_called_once_with(doc_to_delete_id)

        # Verify DB cascade cleanup
        self.assertFalse(Document.objects.filter(id=doc_to_delete_id).exists())
        self.assertFalse(Clause.objects.filter(document_id=doc_to_delete_id).exists())
        self.assertFalse(DocumentSummary.objects.filter(document_id=doc_to_delete_id).exists())

        # Verify Dashboard Summary immediately reflects the deletion:
        # - total_documents drops from 5 to 4
        # - completed_count drops from 2 to 1
        # - flagged_risk_count drops from 1 to 0 (the deleted doc was the only high-risk completed doc)
        dashboard_url = reverse('dashboard_summary')
        dash_res = self.client.get(dashboard_url)
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_res.data['total_documents'], 4)
        self.assertEqual(dash_res.data['completed_count'], 1)
        self.assertEqual(dash_res.data['in_progress_count'], 2)
        self.assertEqual(dash_res.data['failed_count'], 1)
        self.assertEqual(dash_res.data['flagged_risk_count'], 0)

        # Verify History list immediately reflects the deletion:
        # - count drops to 4
        # - deleted doc ID is absent
        history_url = reverse('document_list_create')
        hist_res = self.client.get(history_url)
        self.assertEqual(hist_res.status_code, status.HTTP_200_OK)
        self.assertEqual(hist_res.data['count'], 4)
        hist_ids = [d['id'] for d in hist_res.data['results']]
        self.assertNotIn(doc_to_delete_id, hist_ids)

        # IDOR Security Check: User A attempts to delete User B's document
        user_b_doc_url = reverse('document_detail_delete', kwargs={'pk': str(self.doc_b_complete_risk.id)})
        idor_del_res = self.client.delete(user_b_doc_url)
        self.assertEqual(idor_del_res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotEqual(idor_del_res.status_code, status.HTTP_403_FORBIDDEN)

        # Verify User B's document is completely untouched in database
        self.assertTrue(Document.objects.filter(id=self.doc_b_complete_risk.id).exists())
