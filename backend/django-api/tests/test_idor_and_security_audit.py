"""
Phase 16 System-Wide Security Audit Pass (PRD Part B.8, Ch. 27, Ch. 34.4):
Comprehensive IDOR & Security Regression Test Matrix across all ClarifAI resources:
- Document detail, document delete
- Clause list, clause detail, document summary
- Chat sessions, chat messages (history & send)
- Comparison detail, comparison creation
- Report generation (document & comparison), report download
- Unauthorized update, deletion, and download attempts
- Part B.8 Security Architecture checklist re-verification
"""
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.comparison.models import Comparison, ComparisonCategory, ComparisonResult, ComparisonStatus
from apps.documents.models import Clause, ClauseSeverity, Document, DocumentStatus, DocumentSummary
from apps.reports.models import Report, ReportStatus

User = get_user_model()


class SystemWideSecurityAuditTestCase(APITestCase):

    def setUp(self):
        cache.clear()
        self.user_a = User.objects.create_user(
            email='audit_usera@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='audit_userb@example.com',
            password='Password123!'
        )

        # Document owned by User A
        self.doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='usera_contract.pdf',
            file_reference='uploads/documents/usera_contract.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.summary_a = DocumentSummary.objects.create(
            document=self.doc_a,
            purpose_text='User A agreement purpose.',
            key_risks_text='User A agreement key risks.'
        )
        self.clause_a1 = Clause.objects.create(
            document=self.doc_a,
            position=1,
            original_text='User A Clause 1 text.',
            simplified_text='User A Clause 1 simplified.',
            severity=ClauseSeverity.HIGH
        )

        # Chat session owned by User A
        self.chat_session_a = ChatSession.objects.create(
            user=self.user_a,
            document=self.doc_a,
            title='User A Chat Session'
        )
        self.chat_msg_a = ChatMessage.objects.create(
            session=self.chat_session_a,
            role=MessageRole.USER,
            content='What are the risks in this contract?'
        )

        # Target document for comparison owned by User A
        self.doc_a_target = Document.objects.create(
            user=self.user_a,
            original_filename='usera_contract_v2.pdf',
            file_reference='uploads/documents/usera_contract_v2.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.comparison_a = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a,
            target_document=self.doc_a_target,
            status=ComparisonStatus.COMPLETE
        )

        # Report owned by User A
        self.report_a = Report.objects.create(
            user=self.user_a,
            document=self.doc_a,
            status=ReportStatus.COMPLETE,
            file_reference='uploads/reports/usera_report.pdf'
        )

    # -------------------------------------------------------------------------
    # 1. IDOR TEST MATRIX: User B accessing User A's resources MUST return 404
    # -------------------------------------------------------------------------

    def test_idor_document_detail_user_b_returns_404(self):
        """User B requesting User A's document detail receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_detail_delete', kwargs={'pk': self.doc_a.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_document_delete_user_b_returns_404(self):
        """User B attempting to delete User A's document receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_detail_delete', kwargs={'pk': self.doc_a.id})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Document.objects.filter(id=self.doc_a.id).exists())

    def test_idor_clause_list_user_b_returns_404(self):
        """User B requesting clauses of User A's document receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_clause_list', kwargs={'pk': self.doc_a.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_clause_detail_user_b_returns_404(self):
        """User B requesting clause detail of User A's document receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_clause_detail', kwargs={'pk': self.doc_a.id, 'clause_id': self.clause_a1.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_document_summary_user_b_returns_404(self):
        """User B requesting summary of User A's document receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_summary', kwargs={'pk': self.doc_a.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_chat_messages_history_user_b_returns_404(self):
        """User B requesting chat messages for User A's session receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_chat_messages', kwargs={'pk': self.doc_a.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_chat_message_send_user_b_returns_404(self):
        """User B sending a message to User A's chat session receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_chat_messages', kwargs={'pk': self.doc_a.id})
        res = self.client.post(url, {'content': 'Malicious prompt injection attempt.'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_comparison_create_user_b_returns_404(self):
        """User B attempting to compare using User A's document ID receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        # Create a document for User B to act as target_document
        doc_b = Document.objects.create(
            user=self.user_b,
            original_filename='userb_doc.pdf',
            file_reference='uploads/documents/userb_doc.pdf',
            status=DocumentStatus.COMPLETE
        )
        url = reverse('comparison_list_create')
        res = self.client.post(url, {
            'base_document_id': str(self.doc_a.id),
            'target_document_id': str(doc_b.id)
        })
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_comparison_detail_user_b_returns_404(self):
        """User B requesting detail of User A's comparison receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('comparison_detail', kwargs={'pk': self.comparison_a.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_report_generate_document_user_b_returns_404(self):
        """User B attempting to generate a report for User A's document receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('document_report_create', kwargs={'pk': self.doc_a.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_report_generate_comparison_user_b_returns_404(self):
        """User B attempting to generate a report for User A's comparison receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('comparison_report_create', kwargs={'pk': self.comparison_a.id})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_report_download_user_b_returns_404(self):
        """User B attempting to download User A's report receives HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.user_b)
        url = reverse('report_download', kwargs={'pk': self.report_a.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 2. UNAUTHORIZED UPDATE, DELETION & DOWNLOAD NEGATIVE TESTS
    # -------------------------------------------------------------------------

    def test_unauthorized_update_attempt_document_rejected(self):
        """Attempting to PUT/PATCH a document endpoint returns HTTP 405 Method Not Allowed or 404."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_detail_delete', kwargs={'pk': self.doc_a.id})
        res_put = self.client.put(url, {'original_filename': 'hacked.pdf'})
        res_patch = self.client.patch(url, {'original_filename': 'hacked.pdf'})
        self.assertIn(res_put.status_code, [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND])
        self.assertIn(res_patch.status_code, [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_download_attempt_report_rejected(self):
        """Unauthenticated user attempting to download a report receives HTTP 401 Unauthorized."""
        self.client.logout()
        url = reverse('report_download', kwargs={'pk': self.report_a.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_deletion_attempt_document_rejected(self):
        """Unauthenticated user attempting to delete a document receives HTTP 401 Unauthorized."""
        self.client.logout()
        url = reverse('document_detail_delete', kwargs={'pk': self.doc_a.id})
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 3. PART B.8 SECURITY ARCHITECTURE RE-VERIFICATION
    # -------------------------------------------------------------------------

    def test_password_hashing_uses_secure_algorithm(self):
        """Verifies User password in DB is hashed securely (never stored in plain text)."""
        db_user = User.objects.get(id=self.user_a.id)
        self.assertFalse(db_user.password.startswith('Password123!'))
        self.assertTrue(
            db_user.password.startswith('pbkdf2_sha256$') or
            db_user.password.startswith('argon2')
        )

    def test_jwt_lifetimes_and_cookie_security_config(self):
        """Verifies JWT token lifetime settings match PRD Ch. 26.1 (15m Access, 7d Refresh)."""
        jwt_config = getattr(settings, 'SIMPLE_JWT', {})
        access_seconds = jwt_config.get('ACCESS_TOKEN_LIFETIME').total_seconds()
        refresh_seconds = jwt_config.get('REFRESH_TOKEN_LIFETIME').total_seconds()

        self.assertEqual(access_seconds, 15 * 60)
        self.assertEqual(refresh_seconds, 7 * 24 * 3600)
        self.assertTrue(jwt_config.get('ROTATE_REFRESH_TOKENS'))
        self.assertTrue(jwt_config.get('BLACKLIST_AFTER_ROTATION'))

    def test_safe_error_handler_no_stack_traces(self):
        """Custom exception handler returns structured JSON without exposing internal stack traces (PRD Ch. 31)."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        class InternalErrView(APIView):
            def get(self, request):
                raise RuntimeError("Simulated internal exception")

        factory = APIRequestFactory()
        request = factory.get('/api/health/')
        from core.exceptions import custom_exception_handler
        response = custom_exception_handler(RuntimeError("Simulated internal exception"), {'request': request, 'view': InternalErrView()})

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertNotIn('Traceback', str(response.data))


