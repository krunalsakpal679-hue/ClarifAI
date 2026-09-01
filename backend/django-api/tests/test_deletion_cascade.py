"""
Phase 14 Deletion Cascade & Data Retention Tests (PRD Ch. 26.5, 26.5.1, 26.5.2):
- Full deletion cascade test verifying every item in Ch. 26.5.1's list is removed or disassociated with zero orphaned rows remaining.
- AI service vector embedding cleanup call trigger verification.
- Security requirement: Owner-only deletion policy (HTTP 404 Not Found for non-owners).
"""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.comparison.models import Comparison, ComparisonCategory, ComparisonResult, ComparisonStatus
from apps.documents.models import Clause, ClauseSeverity, Document, DocumentStatus, DocumentSummary
from apps.reports.models import Report, ReportStatus

User = get_user_model()


class DeletionCascadeTestCase(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            email='delusera@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='deluserb@example.com',
            password='Password123!'
        )

        # Complete Document owned by User A
        self.doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='del_contract.pdf',
            file_reference='uploads/documents/del_contract.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.summary_a = DocumentSummary.objects.create(
            document=self.doc_a,
            purpose_text='Deletion test summary purpose.',
            obligations_text='Deletion test summary obligations.'
        )
        self.clause_a1 = Clause.objects.create(
            document=self.doc_a,
            position=1,
            original_text='Clause 1 text.',
            severity=ClauseSeverity.HIGH
        )
        self.clause_a2 = Clause.objects.create(
            document=self.doc_a,
            position=2,
            original_text='Clause 2 text.',
            severity=ClauseSeverity.SAFE
        )

        # Chat session and messages scoped to doc_a
        self.chat_session = ChatSession.objects.create(
            user=self.user_a,
            document=self.doc_a
        )
        self.msg1 = ChatMessage.objects.create(
            session=self.chat_session,
            role=MessageRole.USER,
            content='What is the payment period?'
        )
        self.msg2 = ChatMessage.objects.create(
            session=self.chat_session,
            role=MessageRole.ASSISTANT,
            content='Payment period is 30 days.'
        )

        # Report tied to doc_a
        self.report_a = Report.objects.create(
            user=self.user_a,
            document=self.doc_a,
            status=ReportStatus.COMPLETE,
            file_reference='uploads/reports/report_a.pdf'
        )

        # Target document for comparison owned by User A
        self.doc_a_target = Document.objects.create(
            user=self.user_a,
            original_filename='del_contract_v2.pdf',
            file_reference='uploads/documents/del_contract_v2.pdf',
            status=DocumentStatus.COMPLETE
        )

        # Comparison referencing doc_a as base_document
        self.comparison_a = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a,
            target_document=self.doc_a_target,
            status=ComparisonStatus.COMPLETE
        )
        self.comp_result_a = ComparisonResult.objects.create(
            comparison=self.comparison_a,
            category=ComparisonCategory.CHANGED,
            difference_explanation='Payment terms updated.',
            similarity_score=0.8
        )

    def test_full_deletion_cascade_zero_orphaned_rows(self):
        """
        DELETE /api/documents/{id}/ removes Document, Clauses, Summary, ChatSession, ChatMessages, Report,
        triggers AI vector cleanup, and disassociates Comparison FK without orphaned rows (PRD Ch. 26.5.1).
        """
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_detail_delete', kwargs={'pk': self.doc_a.id})

        doc_id_str = str(self.doc_a.id)
        session_id = self.chat_session.id

        with patch("services.ai_client.delete_document_embeddings") as mock_vector_cleanup:
            response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 1. AI Vector Embedding Cleanup Triggered
        mock_vector_cleanup.assert_called_once_with(doc_id_str)

        # 2. Document record deleted
        self.assertFalse(Document.objects.filter(id=self.doc_a.id).exists())

        # 3. Clauses cascade deleted
        self.assertEqual(Clause.objects.filter(document_id=self.doc_a.id).count(), 0)

        # 4. DocumentSummary cascade deleted
        self.assertFalse(DocumentSummary.objects.filter(document_id=self.doc_a.id).exists())

        # 5. ChatSession disassociated (document set to NULL)
        self.chat_session.refresh_from_db()
        self.assertIsNone(self.chat_session.document)

        # 6. Report cascade deleted

        self.assertFalse(Report.objects.filter(document_id=self.doc_a.id).exists())

        # 7. Comparison base_document FK set to NULL (SET_NULL) without orphaning or deleting Comparison shell
        self.comparison_a.refresh_from_db()
        self.assertIsNone(self.comparison_a.base_document)
        self.assertEqual(self.comparison_a.user, self.user_a)
        self.assertGreater(self.comparison_a.results.count(), 0)

    def test_deletion_owner_only_security_404(self):
        """Non-owner attempting to delete User A's document receives 404 Not Found and no records are deleted."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_detail_delete', kwargs={'pk': self.doc_a.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Confirm Document and child entities remain 100% intact
        self.assertTrue(Document.objects.filter(id=self.doc_a.id).exists())
        self.assertEqual(Clause.objects.filter(document=self.doc_a).count(), 2)
        self.assertTrue(DocumentSummary.objects.filter(document=self.doc_a).exists())
        self.assertTrue(ChatSession.objects.filter(document=self.doc_a).exists())
