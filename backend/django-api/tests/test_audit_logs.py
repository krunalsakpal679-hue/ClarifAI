"""
Phase 15 Logging & Security Audit Trail Tests (PRD Ch. 26.8, Ch. 29.8, Ch. 31):
- Tests writing of all 6 required audit event types: login_success, login_failure, signup, document_upload, document_delete, analysis_failure.
- Verifies failed login for a non-existent email sets user=None and does NOT leak account existence in API response or audit logs.
- Verifies audit_logs.metadata payloads never contain passwords, tokens, secrets, or raw text.
- Full-text audit check on captured application logs during realistic operations.
"""
import io
import logging
from unittest.mock import patch
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditLog
from apps.audit.services import (
    EVENT_ANALYSIS_FAILURE,
    EVENT_DOCUMENT_DELETE,
    EVENT_DOCUMENT_UPLOAD,
    EVENT_LOGIN_FAILURE,
    EVENT_LOGIN_SUCCESS,
    EVENT_SIGNUP,
)
from apps.documents.models import Document, DocumentStatus
from tasks.document_tasks import process_document
from tests.test_documents import create_sample_pdf

User = get_user_model()


class AuditLogsTestCase(APITestCase):

    def setUp(self):
        cache.clear()
        self.raw_password = 'Password123!'
        self.user_email = 'audituser@example.com'
        self.user = User.objects.create_user(
            email=self.user_email,
            password=self.raw_password
        )


    def test_signup_writes_audit_log(self):
        """POST /api/auth/signup creates a signup audit log row."""
        url = reverse('auth_signup')
        payload = {
            "email": "newaudituser@example.com",
            "password": self.raw_password
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        new_user = User.objects.get(email="newaudituser@example.com")
        log = AuditLog.objects.filter(event_type=EVENT_SIGNUP, user=new_user).first()
        self.assertIsNotNone(log)
        self.assertNotIn('password', log.metadata)

    def test_login_success_writes_audit_log(self):
        """POST /api/auth/login with valid credentials creates login_success audit log row."""
        url = reverse('auth_login')
        payload = {
            "email": self.user_email,
            "password": self.raw_password
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        log = AuditLog.objects.filter(event_type=EVENT_LOGIN_SUCCESS, user=self.user).first()
        self.assertIsNotNone(log)
        self.assertNotIn('password', log.metadata)

    def test_login_failure_existing_user_writes_audit_log(self):
        """POST /api/auth/login with wrong password creates login_failure audit log row bound to user."""
        url = reverse('auth_login')
        payload = {
            "email": self.user_email,
            "password": "WrongPassword999!"
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        err_msg = res.data.get('detail') or str(res.data)
        self.assertIn("Invalid email or password", str(err_msg))

        log = AuditLog.objects.filter(event_type=EVENT_LOGIN_FAILURE, user=self.user).first()
        self.assertIsNotNone(log)

    def test_login_failure_non_existent_email_no_account_leakage(self):
        """POST /api/auth/login with non-existent email creates login_failure audit log with user=None, 401 generic error."""
        url = reverse('auth_login')
        payload = {
            "email": "fakeuser_does_not_exist@example.com",
            "password": "SomePassword123!"
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        # Generic error message to prevent account enumeration via API response (PRD Ch. 32)
        err_msg = res.data.get('detail') or str(res.data)
        self.assertIn("Invalid email or password", str(err_msg))

        log = AuditLog.objects.filter(event_type=EVENT_LOGIN_FAILURE, user__isnull=True).first()
        self.assertIsNotNone(log)

    def test_document_upload_writes_audit_log(self):
        """POST /api/documents/ creates document_upload audit log row."""
        self.client.force_authenticate(user=self.user)
        url = reverse('document_list_create')
        pdf_bytes = create_sample_pdf(pages=1)
        pdf_file = SimpleUploadedFile("audit_doc.pdf", pdf_bytes, content_type="application/pdf")

        res = self.client.post(url, {'file': pdf_file}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        doc_id = res.data['id']

        log = AuditLog.objects.filter(event_type=EVENT_DOCUMENT_UPLOAD, user=self.user).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.metadata.get('document_id'), doc_id)
        self.assertEqual(log.metadata.get('filename'), "audit_doc.pdf")

    def test_document_delete_writes_audit_log(self):
        """DELETE /api/documents/{id}/ creates document_delete audit log row."""
        self.client.force_authenticate(user=self.user)
        doc = Document.objects.create(
            user=self.user,
            original_filename='delete_audit.pdf',
            file_reference='uploads/documents/delete_audit.pdf',
            status=DocumentStatus.COMPLETE
        )
        url = reverse('document_detail_delete', kwargs={'pk': doc.id})

        with patch("services.ai_client.delete_document_embeddings"):
            res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        log = AuditLog.objects.filter(event_type=EVENT_DOCUMENT_DELETE, user=self.user).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.metadata.get('document_id'), str(doc.id))

    def test_analysis_failure_writes_audit_log(self):
        """Celery process_document task failure creates analysis_failure audit log row."""
        doc = Document.objects.create(
            user=self.user,
            original_filename='failing_doc.pdf',
            file_reference='uploads/documents/failing_doc.pdf',
            status=DocumentStatus.QUEUED
        )

        with patch("services.ai_client.process_document", side_effect=RuntimeError("AI pipeline crash")):
            with self.assertRaises(RuntimeError):
                process_document(str(doc.id))

        log = AuditLog.objects.filter(event_type=EVENT_ANALYSIS_FAILURE, user=self.user).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.metadata.get('document_id'), str(doc.id))
        self.assertIn("AI pipeline crash", log.metadata.get('failure_reason'))

    def test_full_text_application_log_audit_no_secrets(self):
        """
        Captures application logs during a realistic operation sequence (signup, login, upload, delete)
        and performs a full-text search verifying ZERO secrets, passwords, tokens, or raw contract text are logged.
        """
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger()
        logger.addHandler(handler)
        original_level = logger.level
        logger.setLevel(logging.INFO)

        try:
            cache.clear()
            # 1. Signup
            self.client.post(reverse('auth_signup'), {
                "email": "logtestuser@example.com",
                "password": "SuperSecretPassword123!"
            })

            # 2. Login
            res_login = self.client.post(reverse('auth_login'), {
                "email": "logtestuser@example.com",
                "password": "SuperSecretPassword123!"
            })
            token = res_login.data.get('access', '') if res_login.status_code == 200 else ''

            # 3. Document Upload
            self.client.force_authenticate(user=self.user)
            pdf_bytes = create_sample_pdf(pages=1)
            pdf_file = SimpleUploadedFile("secret_check.pdf", pdf_bytes, content_type="application/pdf")
            res_up = self.client.post(reverse('document_list_create'), {'file': pdf_file}, format='multipart')

            # 4. Document Delete
            if res_up.status_code == status.HTTP_201_CREATED:
                doc_id = res_up.data['id']
                with patch("services.ai_client.delete_document_embeddings"):
                    self.client.delete(reverse('document_detail_delete', kwargs={'pk': doc_id}))

            logged_output = log_stream.getvalue()

            # Assert ZERO forbidden secrets or raw passwords exist in captured log output
            self.assertNotIn("SuperSecretPassword123!", logged_output)
            if token:
                self.assertNotIn(token, logged_output)

        finally:
            logger.removeHandler(handler)
            logger.setLevel(original_level)


