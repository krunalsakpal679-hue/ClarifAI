"""
Phase 11 Document Comparison Service & Difference Tracking Tests:
- POST /api/comparisons (end-to-end comparison execution against MockAIClient)
- Double-ownership check (404 for unowned base or target document)
- Same-document comparison rejection (400 Bad Request)
- Incomplete document comparison rejection (422 DOCUMENT_NOT_READY)
- Mid-flight document deletion handling (clean FAILED state, no crash)
- GET /api/comparisons/{id} (status, results, IsOwner 404 enforcement)
"""
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comparison.models import Comparison, ComparisonCategory, ComparisonStatus
from apps.documents.models import Document, DocumentStatus
from tasks.comparison_tasks import process_comparison

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=True,
)
class ComparisonEndpointsTestCase(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            email='compusera@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='compuserb@example.com',
            password='Password123!'
        )

        # Completed documents owned by User A
        self.doc_a1 = Document.objects.create(
            user=self.user_a,
            original_filename='usera_v1.pdf',
            file_reference='uploads/documents/usera_v1.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.doc_a2 = Document.objects.create(
            user=self.user_a,
            original_filename='usera_v2.pdf',
            file_reference='uploads/documents/usera_v2.pdf',
            status=DocumentStatus.COMPLETE
        )

        # Completed document owned by User B
        self.doc_b1 = Document.objects.create(
            user=self.user_b,
            original_filename='userb_contract.pdf',
            file_reference='uploads/documents/userb_contract.pdf',
            status=DocumentStatus.COMPLETE
        )

        # Incomplete document owned by User A
        self.incomplete_doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='usera_processing.pdf',
            file_reference='uploads/documents/usera_processing.pdf',
            status=DocumentStatus.EXTRACTING
        )

    def test_create_comparison_success_end_to_end(self):
        """POST /api/comparisons creates pending comparison and executes Celery task end-to-end against MockAIClient."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('comparison_list_create')
        payload = {
            "document_a_id": str(self.doc_a1.id),
            "document_b_id": str(self.doc_a2.id)
        }

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comp_id = response.data['id']

        # Eager Celery task has run, so status should be COMPLETE
        comp = Comparison.objects.get(id=comp_id)
        self.assertEqual(comp.status, ComparisonStatus.COMPLETE)
        self.assertGreater(comp.results.count(), 0)

        # Verify detail endpoint GET /api/comparisons/{id}
        url_detail = reverse('comparison_detail', kwargs={'pk': comp_id})
        res_detail = self.client.get(url_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['status'], 'complete')
        self.assertGreater(len(res_detail.data['results']), 0)

    def test_double_ownership_check_non_owned_rejected(self):
        """POST /api/comparisons fails with 404 if User A attempts to compare User A's doc with User B's doc."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('comparison_list_create')
        payload = {
            "document_a_id": str(self.doc_a1.id),
            "document_b_id": str(self.doc_b1.id)  # Owned by User B
        }

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_same_document_comparison_rejected(self):
        """POST /api/comparisons fails with 400 Bad Request if comparing a document against itself."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('comparison_list_create')
        payload = {
            "document_a_id": str(self.doc_a1.id),
            "document_b_id": str(self.doc_a1.id)  # Same document
        }

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_incomplete_document_comparison_rejected(self):
        """POST /api/comparisons fails with 422 DOCUMENT_NOT_READY if either document is not complete."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('comparison_list_create')
        payload = {
            "document_a_id": str(self.doc_a1.id),
            "document_b_id": str(self.incomplete_doc_a.id)
        }

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['error']['code'], 'DOCUMENT_NOT_READY')

    def test_mid_flight_document_deletion_handled_cleanly(self):
        """If a referenced document is deleted mid-flight, Celery task transitions status to FAILED without crashing."""
        comp = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a1,
            target_document=self.doc_a2,
            status=ComparisonStatus.PENDING
        )

        # Delete target document before processing task runs
        self.doc_a2.delete()

        res = process_comparison(str(comp.id))
        self.assertEqual(res['status'], 'failed')

        comp.refresh_from_db()
        self.assertEqual(comp.status, ComparisonStatus.FAILED)

    def test_get_comparison_detail_non_owned_returns_404(self):
        """GET /api/comparisons/{id} returns 404 Not Found if requested by non-owner."""
        comp = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a1,
            target_document=self.doc_a2,
            status=ComparisonStatus.COMPLETE
        )

        self.client.force_authenticate(user=self.user_b)
        url = reverse('comparison_detail', kwargs={'pk': comp.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_multilingual_fallback_flag(self):
        """GET /api/comparisons/{id}?lang=hi returns translation_available: False when fallback text is served."""
        comp = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a1,
            target_document=self.doc_a2,
            status=ComparisonStatus.COMPLETE
        )

        self.client.force_authenticate(user=self.user_a)
        url = reverse('comparison_detail', kwargs={'pk': comp.id}) + '?lang=hi'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['translation_available'])
