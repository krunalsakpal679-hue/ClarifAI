"""
Phase 9 Risk Classification API, Clause Analysis & Summary Endpoints Tests:
- GET /api/documents/{id}/summary (complete -> 200, incomplete -> 422, non-owned -> 404)
- GET /api/documents/{id}/clauses (complete -> 200, ?severity= filter, rule_findings exposure)
- GET /api/documents/{id}/clauses/{clauseId} (single detail)
- Multilingual fallback flag (lang=hi -> translation_available: False)
- Distinct classification-failure state representation (status: "failed", severity: null)
- Ownership & IDOR 404 enforcement
"""
import uuid
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import (
    Clause,
    ClauseCategory,
    ClauseSeverity,
    ClauseStatus,
    Document,
    DocumentStatus,
    DocumentSummary,
)

User = get_user_model()


class AnalysisEndpointsTestCase(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner9@example.com',
            password='Password123!'
        )
        self.other_user = User.objects.create_user(
            email='other9@example.com',
            password='Password123!'
        )

        # Completed document owned by self.owner
        self.completed_doc = Document.objects.create(
            user=self.owner,
            original_filename='completed_contract.pdf',
            file_reference='uploads/documents/completed_contract.pdf',
            status=DocumentStatus.COMPLETE
        )
        self.summary = DocumentSummary.objects.create(
            document=self.completed_doc,
            purpose_text="Master Services Agreement for software licensing.",
            key_risks_text="Unlimited liability in indemnity clause.\nNet 30 payment terms.",
            key_terms_text="Term of 3 years.",
            obligations_text="Monthly performance reporting."
        )

        # Clauses for completed_doc
        self.clause_high = Clause.objects.create(
            document=self.completed_doc,
            position=1,
            original_text="Licensor shall indemnify Licensee against all claims.",
            simplified_text="Licensor covers all legal claims.",
            explanation="High risk indemnity clause without cap.",
            severity=ClauseSeverity.HIGH,
            category=ClauseCategory.LIABILITY,
            status=ClauseStatus.COMPLETE,
            rule_findings=[{"rule_id": "R-101", "risk_score": 0.9, "matched_pattern": "unlimited indemnity"}]
        )
        self.clause_moderate = Clause.objects.create(
            document=self.completed_doc,
            position=2,
            original_text="Payment is due within 30 days of invoice receipt.",
            simplified_text="Pay within 30 days.",
            explanation="Standard Net 30 payment term.",
            severity=ClauseSeverity.MODERATE,
            category=ClauseCategory.PAYMENT,
            status=ClauseStatus.COMPLETE,
            rule_findings=[{"rule_id": "R-202", "risk_score": 0.5, "matched_pattern": "net 30"}]
        )
        self.clause_failed = Clause.objects.create(
            document=self.completed_doc,
            position=3,
            original_text="Malformed text segment that failed OCR.",
            simplified_text="Clause processing failed.",
            explanation="OCR degradation prevented classification.",
            severity=None,
            category=None,
            status=ClauseStatus.FAILED,
            rule_findings=[]
        )

        # Incomplete document owned by self.owner
        self.incomplete_doc = Document.objects.create(
            user=self.owner,
            original_filename='processing_contract.pdf',
            file_reference='uploads/documents/processing_contract.pdf',
            status=DocumentStatus.EXTRACTING
        )

    def test_get_summary_success(self):
        """GET /api/documents/{id}/summary returns 200 OK with summary fields for completed document."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_summary', kwargs={'pk': self.completed_doc.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['document_id']), str(self.completed_doc.id))
        self.assertIn("Master Services Agreement", response.data['purpose_text'])
        self.assertIn("Unlimited liability", response.data['key_risks_text'])
        self.assertTrue(response.data['translation_available'])

    def test_get_summary_incomplete_returns_422(self):
        """GET /api/documents/{id}/summary returns 422 Unprocessable Entity when document is incomplete."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_summary', kwargs={'pk': self.incomplete_doc.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['error']['code'], 'DOCUMENT_NOT_READY')

    def test_get_summary_non_owned_returns_404(self):
        """GET /api/documents/{id}/summary returns 404 Not Found for non-owner (IsOwner 404-not-403)."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('document_summary', kwargs={'pk': self.completed_doc.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_clauses_list_success_and_rule_findings_exposure(self):
        """GET /api/documents/{id}/clauses returns clause list with embedded rule_findings array."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_clause_list', kwargs={'pk': self.completed_doc.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)

        c1 = results[0]
        self.assertEqual(c1['id'], str(self.clause_high.id))
        self.assertEqual(c1['severity'], 'high')
        self.assertEqual(c1['category'], 'Liability')
        self.assertEqual(len(c1['rule_findings']), 1)
        self.assertEqual(c1['rule_findings'][0]['rule_id'], 'R-101')

    def test_get_clauses_severity_filter(self):
        """GET /api/documents/{id}/clauses?severity=high filters clauses to high severity only."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_clause_list', kwargs={'pk': self.completed_doc.id}) + '?severity=high'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['severity'], 'high')

    def test_get_clauses_incomplete_returns_422(self):
        """GET /api/documents/{id}/clauses returns 422 Unprocessable Entity when document is incomplete."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_clause_list', kwargs={'pk': self.incomplete_doc.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['error']['code'], 'DOCUMENT_NOT_READY')


    def test_get_clauses_non_owned_returns_404(self):
        """GET /api/documents/{id}/clauses returns 404 Not Found for non-owner."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('document_clause_list', kwargs={'pk': self.completed_doc.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_clause_detail_success(self):
        """GET /api/documents/{id}/clauses/{clauseId}/ returns single clause detail matching list shape."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_clause_detail', kwargs={
            'pk': self.completed_doc.id,
            'clause_id': self.clause_high.id
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.clause_high.id))
        self.assertEqual(response.data['severity'], 'high')
        self.assertEqual(len(response.data['rule_findings']), 1)

    def test_get_clause_detail_non_owned_returns_404(self):
        """GET /api/documents/{id}/clauses/{clauseId}/ returns 404 Not Found for non-owner."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('document_clause_detail', kwargs={
            'pk': self.completed_doc.id,
            'clause_id': self.clause_high.id
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_multilingual_fallback_flag(self):
        """GET /api/documents/{id}/clauses/?lang=hi returns translation_available: False when fallback text is returned."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_clause_list', kwargs={'pk': self.completed_doc.id}) + '?lang=hi'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertFalse(results[0]['translation_available'])

    def test_failed_clause_represented_distinctly(self):
        """Clause with status = 'failed' renders status: 'failed' and severity: null distinctly (never omitted)."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('document_clause_list', kwargs={'pk': self.completed_doc.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Clause 3 is the failed clause
        failed_clause = [c for c in results if c['id'] == str(self.clause_failed.id)][0]
        self.assertEqual(failed_clause['status'], 'failed')
        self.assertIsNone(failed_clause['severity'])
        self.assertIsNone(failed_clause['category'])
        self.assertEqual(failed_clause['simplified_text'], 'Clause processing failed.')
