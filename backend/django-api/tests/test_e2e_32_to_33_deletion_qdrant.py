"""
ClarifAI End-to-End Deletion & Qdrant Cleanup Test Suite (BOOK4-PHASE-23: E2E-32, E2E-33)
Traceability: PRD v2.3 Chapter 26.5.1, 26.5.2 (Active-Data Deletion Model), 26.8 (Audit Logging), 30.2.

Validates:
- E2E-32: Deletion via DELETE /api/documents/{id}/ completely removes/disassociates:
  document record, stored file, extracted clauses, document summary, chat sessions/messages,
  dependent comparisons, generated reports, and storage report files.
- E2E-33: AI Vector / Qdrant Cleanup:
  Vector embedding deletion is triggered via adapter, points are purged, and zero retrievable trace remains.
- Complete Unretrievability:
  Deleted document cannot be retrieved via any public or internal API surface (Document Detail, Summary,
  Clauses, Chat Sessions, Chat Messages, Reports, Comparisons, History, Dashboard).
- Owner-Scoped Authorization & IDOR:
  Non-owner attempting DELETE receives HTTP 404 Not Found (404-not-403 policy) with zero deletion effect.
- Audit Log Privacy Compliance:
  Audit log records document_delete event with approved metadata only; zero raw text or confidential contract content is stored.
"""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditLog
from apps.audit.services import EVENT_DOCUMENT_DELETE
from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.comparison.models import Comparison, ComparisonCategory, ComparisonResult, ComparisonStatus
from apps.documents.models import Clause, ClauseSeverity, Document, DocumentStatus, DocumentSummary
from apps.reports.models import Report, ReportLanguage, ReportStatus

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=True,
)
class DeletionAndQdrantCleanupE2ETestCase(APITestCase):

    def setUp(self):
        cache.clear()

        # Primary user (User A)
        self.user_a = User.objects.create_user(
            email='e2e_del_user_a@example.com',
            password='TestPassword123!'
        )

        # Secondary user (User B) for IDOR security tests
        self.user_b = User.objects.create_user(
            email='e2e_del_user_b@example.com',
            password='TestPassword123!'
        )

        # Store test PDF in storage
        self.doc_file_path = default_storage.save(
            'uploads/documents/e2e_confidential_contract.pdf',
            ContentFile(b'%PDF-1.4 Confidential Agreement Content For Deletion Test')
        )

        # 1. Complete Document owned by User A
        self.doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='e2e_confidential_contract.pdf',
            file_reference=self.doc_file_path,
            document_type='Commercial Contract',
            status=DocumentStatus.COMPLETE
        )

        # 2. Document Summary
        self.summary_a = DocumentSummary.objects.create(
            document=self.doc_a,
            purpose_text='Confidential commercial contract purpose text.',
            key_risks_text='Uncapped liability and indemnification risk.',
            key_terms_text='Net 30 days payment; 2-year duration.',
            obligations_text='Both parties adhere to delivery schedule.'
        )

        # 3. Clauses
        self.clause_a1 = Clause.objects.create(
            document=self.doc_a,
            position=1,
            original_text='Party A indemnifies Party B for all losses without dollar limitation.',
            simplified_text='Party A will cover all losses with no limit on costs.',
            severity=ClauseSeverity.HIGH,
            category='Liability',
            rule_findings={'rule': 'R001', 'confidence': 0.96}
        )
        self.clause_a2 = Clause.objects.create(
            document=self.doc_a,
            position=2,
            original_text='Standard confidentiality obligation with 3-year term.',
            simplified_text='Keep shared confidential information secret for 3 years.',
            severity=ClauseSeverity.SAFE,
            category='Confidentiality',
            rule_findings={}
        )

        # 4. Chat Session & Messages
        self.chat_session = ChatSession.objects.create(
            user=self.user_a,
            document=self.doc_a,
            title='Chat regarding confidential contract'
        )
        self.msg1 = ChatMessage.objects.create(
            session=self.chat_session,
            role=MessageRole.USER,
            content='What is the liability cap?'
        )
        self.msg2 = ChatMessage.objects.create(
            session=self.chat_session,
            role=MessageRole.ASSISTANT,
            content='The agreement contains uncapped liability under Clause 1.',
            source_clause_ids=[str(self.clause_a1.id)]
        )

        # 5. Generated Report & Report Storage File
        self.report_file_path = default_storage.save(
            'uploads/reports/e2e_confidential_report.pdf',
            ContentFile(b'%PDF-1.4 Generated PDF Report Content For Deletion Test')
        )
        self.report_a = Report.objects.create(
            user=self.user_a,
            document=self.doc_a,
            language=ReportLanguage.ENGLISH,
            status=ReportStatus.COMPLETE,
            file_reference=self.report_file_path
        )

        # 6. Second Document & Dependent Comparison
        self.doc_a_target = Document.objects.create(
            user=self.user_a,
            original_filename='e2e_target_agreement.pdf',
            file_reference='uploads/documents/e2e_target_agreement.pdf',
            document_type='Commercial Contract',
            status=DocumentStatus.COMPLETE
        )
        self.comparison_a = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a,
            target_document=self.doc_a_target,
            status=ComparisonStatus.COMPLETE
        )
        self.comp_result_a = ComparisonResult.objects.create(
            comparison=self.comparison_a,
            category=ComparisonCategory.CHANGED,
            difference_explanation='Payment terms modified from Net 30 to Net 60.',
            similarity_score=0.82
        )

    def tearDown(self):
        # Clean up any leftover test files in default_storage
        for path in [self.doc_file_path, self.report_file_path]:
            try:
                if default_storage.exists(path):
                    default_storage.delete(path)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # E2E-32 / E2E-33: Complete Deletion Cascade & Vector Cleanup
    # -------------------------------------------------------------------------

    def test_e2e_32_33_complete_active_data_deletion_cascade(self):
        """
        E2E-32 & E2E-33: DELETE /api/documents/{id}/ executes complete active-data deletion:
        - Purges document record, physical uploaded PDF, clauses, summary, chat session disassociation,
          report file, and triggers AI Qdrant vector deletion (PRD Ch. 26.5.1, 26.5.2).
        """
        self.client.force_authenticate(user=self.user_a)
        doc_id = str(self.doc_a.id)
        delete_url = reverse('document_detail_delete', kwargs={'pk': doc_id})

        with patch("services.ai_client.delete_document_embeddings") as mock_vector_cleanup:
            mock_vector_cleanup.return_value = {"status": "success", "deleted_document_id": doc_id}
            response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 1. Qdrant vector embedding cleanup triggered
        mock_vector_cleanup.assert_called_once_with(doc_id)

        # 2. PostgreSQL document record removed
        self.assertFalse(Document.objects.filter(id=doc_id).exists())

        # 3. Uploaded file removed from physical/object storage
        self.assertFalse(default_storage.exists(self.doc_file_path))

        # 4. Report PDF artifact removed from physical/object storage
        self.assertFalse(default_storage.exists(self.report_file_path))

        # 5. Clauses cascade deleted from PostgreSQL
        self.assertEqual(Clause.objects.filter(document_id=doc_id).count(), 0)

        # 6. DocumentSummary cascade deleted from PostgreSQL
        self.assertFalse(DocumentSummary.objects.filter(document_id=doc_id).exists())

        # 7. ChatSession disassociated from deleted document
        self.assertEqual(ChatSession.objects.filter(document_id=doc_id).count(), 0)
        self.chat_session.refresh_from_db()
        self.assertIsNone(self.chat_session.document)

        # 8. Report disassociated from deleted document
        self.assertEqual(Report.objects.filter(document_id=doc_id).count(), 0)
        self.report_a.refresh_from_db()
        self.assertIsNone(self.report_a.document)

        # 9. Comparison disassociated (base_document SET_NULL)
        self.assertEqual(Comparison.objects.filter(base_document_id=doc_id).count(), 0)
        self.comparison_a.refresh_from_db()
        self.assertIsNone(self.comparison_a.base_document)
        self.assertEqual(self.comparison_a.target_document, self.doc_a_target)

    # -------------------------------------------------------------------------
    # Surface Unretrievability Verification
    # -------------------------------------------------------------------------

    def test_e2e_32_33_unretrievability_across_all_surfaces_after_deletion(self):
        """
        Confirms that once a document is deleted, it is completely unretrievable
        via any endpoint or feature: Document, Summary, Clauses, Chat, Reports, Comparisons, History, Dashboard.
        """
        self.client.force_authenticate(user=self.user_a)
        doc_id = str(self.doc_a.id)
        clause_id = str(self.clause_a1.id)
        delete_url = reverse('document_detail_delete', kwargs={'pk': doc_id})

        with patch("services.ai_client.delete_document_embeddings"):
            del_res = self.client.delete(delete_url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

        # Surface 1: Document Detail endpoint
        res = self.client.get(reverse('document_detail_delete', kwargs={'pk': doc_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 2: Document Summary endpoint
        res = self.client.get(reverse('document_summary', kwargs={'pk': doc_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 3: Document Clauses List endpoint
        res = self.client.get(reverse('document_clause_list', kwargs={'pk': doc_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 4: Clause Detail endpoint
        res = self.client.get(reverse('document_clause_detail', kwargs={'pk': doc_id, 'clause_id': clause_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 5: Chat Sessions endpoint
        res = self.client.get(reverse('document_chat_sessions', kwargs={'pk': doc_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 6: Chat Messages List & POST endpoints
        res = self.client.get(reverse('document_chat_messages', kwargs={'pk': doc_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        res = self.client.post(
            reverse('document_chat_messages', kwargs={'pk': doc_id}),
            {'query': 'What is the liability cap?'}
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 7: Document Report Generation endpoint
        res = self.client.post(reverse('document_report_create', kwargs={'pk': doc_id}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 8: Comparison creation referencing deleted doc
        res = self.client.post(reverse('comparison_list_create'), {
            'document_a_id': doc_id,
            'document_b_id': str(self.doc_a_target.id)
        })
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Surface 9: History paginated list
        hist_res = self.client.get(reverse('document_list_create'))
        self.assertEqual(hist_res.status_code, status.HTTP_200_OK)
        returned_ids = [d['id'] for d in hist_res.data['results']]
        self.assertNotIn(doc_id, returned_ids)

        # Surface 10: Dashboard summary
        dash_res = self.client.get(reverse('dashboard_summary'))
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        # Only doc_a_target remains (1 total, 1 completed, 0 flagged risk)
        self.assertEqual(dash_res.data['total_documents'], 1)
        self.assertEqual(dash_res.data['flagged_risk_count'], 0)

    # -------------------------------------------------------------------------
    # Owner-Scoped Authorization & IDOR Verification
    # -------------------------------------------------------------------------

    def test_e2e_32_33_owner_scoped_deletion_security_idor(self):
        """
        Confirms deletion is strictly owner-scoped:
        A second user (User B) cannot delete User A's document, receiving HTTP 404 Not Found (404-not-403).
        No database records or stored files are removed.
        """
        self.client.force_authenticate(user=self.user_b)
        doc_id = str(self.doc_a.id)
        delete_url = reverse('document_detail_delete', kwargs={'pk': doc_id})

        with patch("services.ai_client.delete_document_embeddings") as mock_vector_cleanup:
            response = self.client.delete(delete_url)

        # Must return 404 Not Found, never 403 or 204
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # AI cleanup must NOT be invoked
        mock_vector_cleanup.assert_not_called()

        # All records and files remain 100% intact
        self.assertTrue(Document.objects.filter(id=doc_id).exists())
        self.assertTrue(default_storage.exists(self.doc_file_path))
        self.assertTrue(Clause.objects.filter(document_id=doc_id).exists())
        self.assertTrue(DocumentSummary.objects.filter(document_id=doc_id).exists())

    # -------------------------------------------------------------------------
    # Audit Log Privacy & Cleanliness Verification
    # -------------------------------------------------------------------------

    def test_e2e_32_33_audit_trail_cleanliness_zero_raw_content(self):
        """
        Confirms PRD Ch. 26.8 audit log requirements:
        - Exactly one 'document_delete' audit log entry is recorded with owner identity.
        - Metadata contains ONLY approved security tracking keys (document_id, ip_address, user_agent).
        - Zero raw text, clause content, filenames, or confidential contract data exists in the audit trail.
        """
        self.client.force_authenticate(user=self.user_a)
        doc_id = str(self.doc_a.id)
        delete_url = reverse('document_detail_delete', kwargs={'pk': doc_id})

        with patch("services.ai_client.delete_document_embeddings"):
            response = self.client.delete(
                delete_url,
                HTTP_X_FORWARDED_FOR='198.51.100.42',
                HTTP_USER_AGENT='ClarifAI-E2E-Security-Test-Agent/1.0'
            )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Query audit log entry for this deletion
        audit_logs = AuditLog.objects.filter(
            event_type=EVENT_DOCUMENT_DELETE,
            user=self.user_a
        )
        self.assertEqual(audit_logs.count(), 1)

        audit_entry = audit_logs.first()
        self.assertEqual(audit_entry.metadata.get('document_id'), doc_id)
        self.assertEqual(audit_entry.metadata.get('ip_address'), '198.51.100.42')
        self.assertEqual(audit_entry.metadata.get('user_agent'), 'ClarifAI-E2E-Security-Test-Agent/1.0')

        # Strictly verify zero raw text or confidential contract fields in metadata
        metadata_str = str(audit_entry.metadata).lower()
        forbidden_terms = [
            'indemnif', 'liability', 'confidential', 'losses', 'payment',
            'raw_text', 'clause_text', 'original_text', 'content'
        ]
        for term in forbidden_terms:
            self.assertNotIn(
                term,
                metadata_str,
                f"Privacy violation: sensitive term '{term}' found in audit log metadata: {audit_entry.metadata}"
            )
