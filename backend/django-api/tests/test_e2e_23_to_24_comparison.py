"""
ClarifAI End-to-End Comparison Test Suite (BOOK4-PHASE-19: E2E-23, E2E-24)
Validates:
- E2E-23: Pairwise comparison of similar documents with matched/changed/missing categorization
  and grounded difference explanations.
- E2E-24: Pairwise comparison of structurally dissimilar documents with low-confidence indicator
  surfacing without blocking results (PRD Ch. 18.3).
- Self-comparison rejection (HTTP 400 Bad Request).
- Double-ownership enforcement (HTTP 404 Not Found, never partial results).
- IDOR isolation on comparison detail endpoint.
"""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.comparison.models import Comparison, ComparisonCategory, ComparisonStatus
from apps.documents.models import Document, DocumentStatus, Clause
from tasks.comparison_tasks import process_comparison

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=False,
)
class ComparisonE2ETestCase(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            email='e2e_comp_user_a@example.com',
            password='TestPassword123!'
        )
        self.user_b = User.objects.create_user(
            email='e2e_comp_user_b@example.com',
            password='TestPassword123!'
        )

        # Baseline Document A (Master Services Agreement v1)
        self.doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='MSA_v1.pdf',
            file_reference='uploads/documents/MSA_v1.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.clause_a1 = Clause.objects.create(
            document=self.doc_a,
            position=1,
            original_text="Each party agrees to hold Confidential Information in strict confidence for three (3) years.",
            simplified_text="Keep secret information safe for 3 years.",
            severity="Safe"
        )
        self.clause_a2 = Clause.objects.create(
            document=self.doc_a,
            position=2,
            original_text="Supplier liability for breach shall be capped at $100,000.",
            simplified_text="Supplier liability is capped at $100,000.",
            severity="Low"
        )
        self.clause_a3 = Clause.objects.create(
            document=self.doc_a,
            position=3,
            original_text="This agreement is governed by the laws of California.",
            simplified_text="California law governs this contract.",
            severity="Safe"
        )

        # Revised Document B (Master Services Agreement v2 - Similar Pair)
        self.doc_b_similar = Document.objects.create(
            user=self.user_a,
            original_filename='MSA_v2.pdf',
            file_reference='uploads/documents/MSA_v2.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.clause_b1 = Clause.objects.create(
            document=self.doc_b_similar,
            position=1,
            original_text="Each party agrees to hold Confidential Information in strict confidence for three (3) years.",
            simplified_text="Keep secret information safe for 3 years.",
            severity="Safe"
        )
        self.clause_b2 = Clause.objects.create(
            document=self.doc_b_similar,
            position=2,
            original_text="Supplier liability for breach shall be uncapped and unlimited in any event.",
            simplified_text="Supplier liability is completely unlimited.",
            severity="High"
        )
        self.clause_b3 = Clause.objects.create(
            document=self.doc_b_similar,
            position=3,
            original_text="Any dispute shall be submitted to binding arbitration in San Francisco.",
            simplified_text="Disputes must go to arbitration in San Francisco.",
            severity="Safe"
        )

        # Dissimilar Document C (Short Order Form - 1 Clause vs Doc A's 3 Clauses or 5 Clauses)
        self.doc_c_dissimilar = Document.objects.create(
            user=self.user_a,
            original_filename='Short_Order_Form.pdf',
            file_reference='uploads/documents/Short_Order_Form.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.clause_c1 = Clause.objects.create(
            document=self.doc_c_dissimilar,
            position=1,
            original_text="Total fees due upon delivery: $500.",
            simplified_text="Pay $500 when delivered.",
            severity="Safe"
        )

        # Document owned by User B
        self.doc_b_owned_by_user_b = Document.objects.create(
            user=self.user_b,
            original_filename='UserB_Private_Contract.pdf',
            file_reference='uploads/documents/UserB_Private_Contract.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.clause_b_user_b = Clause.objects.create(
            document=self.doc_b_owned_by_user_b,
            position=1,
            original_text="User B confidential agreement.",
            simplified_text="Private to User B.",
            severity="Safe"
        )

    @patch("tasks.comparison_tasks.ai_client.compare")
    def test_e2e_23_compare_similar_pair_categorization_and_grounded_explanations(self, mock_compare):
        """
        E2E-23: Compare a similar pair; confirm changed/matched/missing categorization
        with grounded explanations, accurate counts, and valid foreign key clause references.
        """
        self.client.force_authenticate(user=self.user_a)

        mock_compare.return_value = {
            "success": True,
            "user_id": str(self.user_a.id),
            "document_id_a": str(self.doc_a.id),
            "document_id_b": str(self.doc_b_similar.id),
            "total_clauses_a": 3,
            "total_clauses_b": 3,
            "matched_count": 1,
            "changed_count": 1,
            "missing_count": 1,
            "is_low_confidence": False,
            "confidence_warning": None,
            "comparison_results": [
                {
                    "clause_id_a": str(self.clause_a1.id),
                    "clause_id_b": str(self.clause_b1.id),
                    "position_a": 1,
                    "position_b": 1,
                    "text_a": self.clause_a1.original_text,
                    "text_b": self.clause_b1.original_text,
                    "similarity_score": 0.98,
                    "classification": "MATCHED",
                    "difference_explanation": "Clause content matches baseline across documents with minimal variation."
                },
                {
                    "clause_id_a": str(self.clause_a2.id),
                    "clause_id_b": str(self.clause_b2.id),
                    "position_a": 2,
                    "position_b": 2,
                    "text_a": self.clause_a2.original_text,
                    "text_b": self.clause_b2.original_text,
                    "similarity_score": 0.72,
                    "classification": "CHANGED",
                    "difference_explanation": "Liability cap changed from a $100,000 monetary limit to uncapped, unlimited liability."
                },
                {
                    "clause_id_a": str(self.clause_a3.id),
                    "clause_id_b": None,
                    "position_a": 3,
                    "position_b": None,
                    "text_a": self.clause_a3.original_text,
                    "text_b": None,
                    "similarity_score": 0.21,
                    "classification": "MISSING",
                    "difference_explanation": "Governing law clause from Document A is missing in Document B."
                }
            ],
            "schema_version": "1.0.0"
        }

        url = reverse('comparison_list_create')
        payload = {
            "document_a_id": str(self.doc_a.id),
            "document_b_id": str(self.doc_b_similar.id)
        }
        create_res = self.client.post(url, payload)
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        comp_id = create_res.data['id']

        # Fetch detail endpoint
        url_detail = reverse('comparison_detail', kwargs={'pk': comp_id})
        res = self.client.get(url_detail)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        # 1. State machine completed
        self.assertEqual(data['status'], 'complete')

        # 2. Structural ratio is 1:1, so is_low_confidence is False
        self.assertFalse(data['is_low_confidence'])
        self.assertIsNone(data['confidence_warning'])

        # 3. Categorization counts
        self.assertEqual(data['matched_count'], 1)
        self.assertEqual(data['changed_count'], 1)
        self.assertEqual(data['missing_count'], 1)

        # 4. Results verification
        results = data['results']
        self.assertEqual(len(results), 3)

        categories = {r['category'] for r in results}
        self.assertIn('matched', categories)
        self.assertIn('changed', categories)
        self.assertIn('missing', categories)

        changed_item = next(r for r in results if r['category'] == 'changed')
        self.assertIn('Liability cap changed', changed_item['difference_explanation'])
        self.assertEqual(changed_item['clause_id_a'], str(self.clause_a2.id))
        self.assertEqual(changed_item['clause_id_b'], str(self.clause_b2.id))

    @patch("tasks.comparison_tasks.ai_client.compare")
    def test_e2e_24_compare_dissimilar_pair_low_confidence_indicator(self, mock_compare):
        """
        E2E-24: Compare a dissimilar pair (Doc A has 3 clauses, Doc C has 1 clause, ratio 3.0 > 2.0);
        confirm low-confidence indicator surfaces without blocking the result.
        """
        self.client.force_authenticate(user=self.user_a)

        mock_compare.return_value = {
            "success": True,
            "user_id": str(self.user_a.id),
            "document_id_a": str(self.doc_a.id),
            "document_id_b": str(self.doc_c_dissimilar.id),
            "total_clauses_a": 3,
            "total_clauses_b": 1,
            "matched_count": 0,
            "changed_count": 0,
            "missing_count": 3,
            "is_low_confidence": True,
            "confidence_warning": "Documents differ significantly in structure/length (3 clauses in Doc A vs 1 clauses in Doc B). Pairwise alignment confidence is reduced (PRD Ch. 18.3).",
            "comparison_results": [
                {
                    "clause_id_a": str(self.clause_a1.id),
                    "clause_id_b": None,
                    "position_a": 1,
                    "position_b": None,
                    "text_a": self.clause_a1.original_text,
                    "text_b": None,
                    "similarity_score": 0.1,
                    "classification": "MISSING",
                    "difference_explanation": "Clause absent in Document B."
                }
            ],
            "schema_version": "1.0.0"
        }

        url = reverse('comparison_list_create')
        payload = {
            "document_a_id": str(self.doc_a.id),
            "document_b_id": str(self.doc_c_dissimilar.id)
        }
        create_res = self.client.post(url, payload)
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        comp_id = create_res.data['id']

        url_detail = reverse('comparison_detail', kwargs={'pk': comp_id})
        res = self.client.get(url_detail)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        # Comparison must NOT be blocked: status is complete
        self.assertEqual(data['status'], 'complete')

        # Low-confidence indicator surfaces prominently
        self.assertTrue(data['is_low_confidence'])
        self.assertIsNotNone(data['confidence_warning'])
        self.assertIn("differ significantly", data['confidence_warning'])
        self.assertIn("PRD Ch. 18.3", data['confidence_warning'])

    def test_self_comparison_blocked_with_clear_error(self):
        """
        Attempt self-comparison (comparing document A against document A);
        confirm it is blocked with HTTP 400 and a clear non-field error message.
        """
        self.client.force_authenticate(user=self.user_a)
        url = reverse('comparison_list_create')
        payload = {
            "document_a_id": str(self.doc_a.id),
            "document_b_id": str(self.doc_a.id)
        }

        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = str(res.data)
        self.assertIn("Cannot compare a document against itself", error_msg)

    def test_non_owned_document_comparison_blocked_with_404(self):
        """
        Attempt comparing a non-owned document; confirm a 404-equivalent,
        not a partial result or 403, preventing document ID enumeration.
        """
        self.client.force_authenticate(user=self.user_a)
        url = reverse('comparison_list_create')

        # Case 1: Base document is owned by User A, target document is owned by User B
        payload_1 = {
            "document_a_id": str(self.doc_a.id),
            "document_b_id": str(self.doc_b_owned_by_user_b.id)
        }
        res_1 = self.client.post(url, payload_1)
        self.assertEqual(res_1.status_code, status.HTTP_404_NOT_FOUND)

        # Case 2: Base document is owned by User B, target document is owned by User A
        payload_2 = {
            "document_a_id": str(self.doc_b_owned_by_user_b.id),
            "document_b_id": str(self.doc_a.id)
        }
        res_2 = self.client.post(url, payload_2)
        self.assertEqual(res_2.status_code, status.HTTP_404_NOT_FOUND)

        # Case 3: User B attempts to access a comparison owned by User A
        comp_a = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a,
            target_document=self.doc_b_similar,
            status=ComparisonStatus.COMPLETE
        )
        self.client.force_authenticate(user=self.user_b)
        url_detail = reverse('comparison_detail', kwargs={'pk': comp_a.id})
        res_detail = self.client.get(url_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_404_NOT_FOUND)
