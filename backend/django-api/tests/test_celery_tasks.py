"""
Phase 6 Celery + Redis Task Queue Integration & State Machine Unit & Security Tests:
- Valid state machine transitions succeed
- Invalid state machine transitions raise ValueError
- Task execution drives Document from queued to complete
- Unhandled task exception transitions Document to failed with failure_reason (never stuck)
- Idempotency guard prevents reprocessing complete documents
- Upload endpoint enqueues background processing task
"""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status

from apps.documents.models import Document, DocumentStatus
from tasks.document_tasks import process_document
from tests.test_documents import create_sample_pdf

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://'
)
class CeleryTaskAndStateMachineTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='celerytest@example.com',
            password='Password123!'
        )
        self.doc = Document.objects.create(
            user=self.user,
            original_filename='test_contract.pdf',
            file_reference='uploads/documents/test_contract.pdf',
            status=DocumentStatus.QUEUED
        )

    def test_state_machine_valid_forward_transitions(self):
        """Document transition_to advances through all valid Ch. 15 processing states."""
        sequence = [
            DocumentStatus.EXTRACTING,
            DocumentStatus.OCR,
            DocumentStatus.SEGMENTING,
            DocumentStatus.CLASSIFYING,
            DocumentStatus.SIMPLIFYING,
            DocumentStatus.SUMMARIZING,
            DocumentStatus.INDEXING,
            DocumentStatus.COMPLETE,
        ]
        for next_state in sequence:
            self.doc.transition_to(next_state)
            self.assertEqual(self.doc.status, next_state)

    def test_state_machine_invalid_transitions_rejected(self):
        """Out-of-order or invalid status transitions raise ValueError."""
        # Attempting queued -> complete (skipping intermediate states)
        with self.assertRaises(ValueError):
            self.doc.transition_to(DocumentStatus.COMPLETE)

        # Transition to complete validly
        for state in [
            DocumentStatus.EXTRACTING, DocumentStatus.OCR, DocumentStatus.SEGMENTING,
            DocumentStatus.CLASSIFYING, DocumentStatus.SIMPLIFYING, DocumentStatus.SUMMARIZING,
            DocumentStatus.INDEXING, DocumentStatus.COMPLETE
        ]:
            self.doc.transition_to(state)

        # Post-terminal transition attempt (complete -> extracting) raises ValueError
        with self.assertRaises(ValueError):
            self.doc.transition_to(DocumentStatus.EXTRACTING)

    def test_process_document_task_happy_path(self):
        """process_document task drives document from queued to complete."""
        result = process_document(str(self.doc.id))
        self.assertEqual(result['status'], 'complete')

        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.COMPLETE)
        self.assertIsNone(self.doc.failure_reason)

    def test_process_document_task_failure_handling(self):
        """Unhandled exception in process_document task transitions document to failed with failure_reason."""
        original_transition = Document.transition_to

        def mock_transition(doc_self, new_status, failure_reason=None):
            if new_status == DocumentStatus.OCR:
                raise RuntimeError("Simulated AI service connection failure")
            return original_transition(doc_self, new_status, failure_reason=failure_reason)

        with patch.object(Document, 'transition_to', side_effect=mock_transition, autospec=True):
            with self.assertRaises(RuntimeError):
                process_document(str(self.doc.id))

        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.FAILED)
        self.assertIn("Simulated AI service connection failure", self.doc.failure_reason)

    def test_process_document_idempotency_guard(self):
        """Reprocessing an already-complete document is an idempotent no-op."""
        # Drive document to complete
        process_document(str(self.doc.id))
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.COMPLETE)

        # Second invocation on complete document
        result = process_document(str(self.doc.id))
        self.assertEqual(result['status'], 'already_complete')

    def test_upload_endpoint_triggers_celery_task(self):
        """POST /api/documents/ enqueues process_document task and drives document processing."""
        login_res = self.client.post(
            '/api/auth/login',
            data={'email': 'celerytest@example.com', 'password': 'Password123!'},
            content_type='application/json'
        )
        token = login_res.json()['access']

        pdf_bytes = create_sample_pdf()
        uploaded_file = SimpleUploadedFile('async_contract.pdf', pdf_bytes, content_type='application/pdf')

        response = self.client.post(
            '/api/documents/',
            data={'file': uploaded_file},
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc_id = response.json()['id']

        # Under CELERY_TASK_ALWAYS_EAGER=True, task executed synchronously during request
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, DocumentStatus.COMPLETE)
