"""
Django Core Cross-Document Isolation & Non-Contamination Regression Test Suite
(PRD Chapters 15, 16.5, 28.4, 28.5, 34, 50, 56.9)

Validates that when two distinct documents with non-overlapping contractual facts
are processed through Django document tasks or queried via REST API endpoints:
1. Zero fields, strings, or numbers from Document X appear in Document Y's stored Clause, DocumentSummary, or API responses.
2. Zero fields, strings, or numbers from Document Y appear in Document X's stored Clause, DocumentSummary, or API responses.
3. Database and Celery task execution maintain absolute isolation.
"""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.documents.models import (
    Clause,
    ClauseStatus,
    Document,
    DocumentStatus,
    DocumentSummary,
)
from tasks.document_tasks import process_document

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=False,
)
class CrossDocumentIsolationTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='isolation_test_user@example.com',
            password='Password123!'
        )
        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

        self.doc_x = Document.objects.create(
            user=self.user,
            original_filename='Document_X_Cloud_Agreement.pdf',
            file_reference='sample_documents/doc_x.pdf',
            status=DocumentStatus.QUEUED
        )
        self.doc_y = Document.objects.create(
            user=self.user,
            original_filename='Document_Y_Maritime_Agreement.pdf',
            file_reference='sample_documents/doc_y.pdf',
            status=DocumentStatus.QUEUED
        )

        self.doc_x_payload = {
            "document_id": str(self.doc_x.id),
            "summary": {
                "purpose_text": "Cloud Infrastructure Service Agreement between Acrobat Cloud Technologies and Beacon Financial Services.",
                "key_risks_text": "Liability capped at $1,250,000 with carve-outs for breach of data security.",
                "key_terms_text": "Net 75 days payment terms with 4.25% late fees.",
                "obligations_text": "Governed by King County, Washington courts."
            },
            "clauses": [
                {
                    "position": 1,
                    "clause_id": "c-001",
                    "severity": "safe",
                    "category": "Liability",
                    "original_text": "Acrobat Cloud Technologies shall provide telemetry analytics.",
                    "simplified_text": "Acrobat Cloud Technologies provides telemetry analytics for Beacon Financial.",
                    "structured_explanation": {
                        "what_this_clause_means": "Defines telemetry analytics services by Acrobat Cloud Technologies for Beacon Financial.",
                        "risk": {"severity": "Safe", "reason": "Standard operational terms."},
                        "category": {"label": "Liability", "reason": "Allocates services."}
                    },
                    "status": "complete"
                },
                {
                    "position": 2,
                    "clause_id": "c-002",
                    "severity": "high",
                    "category": "Liability",
                    "original_text": "Liability cap of $1,250,000 except for breach of data security.",
                    "simplified_text": "Damages capped at $1,250,000 except for breach of data security.",
                    "structured_explanation": {
                        "what_this_clause_means": "Strict ceiling of $1,250,000 with breach of data security uncapped.",
                        "risk": {"severity": "High", "reason": "Financial liability cap with carve-out."},
                        "category": {"label": "Liability", "reason": "Liability cap."}
                    },
                    "status": "complete"
                }
            ]
        }

        self.doc_y_payload = {
            "document_id": str(self.doc_y.id),
            "summary": {
                "purpose_text": "Maritime Logistics Agreement between Zenith Marine Logistics and Apex Harbor Operators.",
                "key_risks_text": "Liability capped at $840,000 with carve-outs for breach of confidentiality.",
                "key_terms_text": "Net 120 days payment terms with 1.75% late fees.",
                "obligations_text": "Governed by Orange County, Florida courts."
            },
            "clauses": [
                {
                    "position": 1,
                    "clause_id": "c-001",
                    "severity": "safe",
                    "category": "Liability",
                    "original_text": "Zenith Marine Logistics shall provide port navigation advisory.",
                    "simplified_text": "Zenith Marine Logistics provides navigation advisory for Apex Harbor.",
                    "structured_explanation": {
                        "what_this_clause_means": "Defines navigation advisory by Zenith Marine Logistics for Apex Harbor.",
                        "risk": {"severity": "Safe", "reason": "Standard operational terms."},
                        "category": {"label": "Liability", "reason": "Allocates services."}
                    },
                    "status": "complete"
                },
                {
                    "position": 2,
                    "clause_id": "c-002",
                    "severity": "high",
                    "category": "Liability",
                    "original_text": "Liability cap of $840,000 except for breach of confidentiality.",
                    "simplified_text": "Damages capped at $840,000 except for breach of confidentiality.",
                    "structured_explanation": {
                        "what_this_clause_means": "Strict ceiling of $840,000 with breach of confidentiality uncapped.",
                        "risk": {"severity": "High", "reason": "Financial liability cap with carve-out."},
                        "category": {"label": "Liability", "reason": "Liability cap."}
                    },
                    "status": "complete"
                }
            ]
        }

    def test_back_to_back_document_processing_and_db_isolation(self):
        """
        Executes process_document for Doc X then Doc Y and verifies zero cross-document data leakage in DB.
        """
        def mock_process_doc(document_id, file_reference, user_id=None):
            if str(document_id) == str(self.doc_x.id):
                return self.doc_x_payload
            elif str(document_id) == str(self.doc_y.id):
                return self.doc_y_payload
            raise ValueError("Unknown doc")

        with patch('services.ai_client.process_document', side_effect=mock_process_doc):
            res_x = process_document(str(self.doc_x.id))
            res_y = process_document(str(self.doc_y.id))

        self.assertEqual(res_x['status'], 'complete')
        self.assertEqual(res_y['status'], 'complete')

        # 1. Check Document X DB records
        sum_x = DocumentSummary.objects.get(document=self.doc_x)
        clauses_x = list(Clause.objects.filter(document=self.doc_x).order_by('position'))
        x_all_text = f"{sum_x.purpose_text} {sum_x.key_risks_text} {sum_x.key_terms_text} {sum_x.obligations_text} " + " ".join(
            f"{c.original_text} {c.simplified_text} {str(c.structured_explanation)}" for c in clauses_x
        )

        # 2. Check Document Y DB records
        sum_y = DocumentSummary.objects.get(document=self.doc_y)
        clauses_y = list(Clause.objects.filter(document=self.doc_y).order_by('position'))
        y_all_text = f"{sum_y.purpose_text} {sum_y.key_risks_text} {sum_y.key_terms_text} {sum_y.obligations_text} " + " ".join(
            f"{c.original_text} {c.simplified_text} {str(c.structured_explanation)}" for c in clauses_y
        )

        # Assert zero Doc X facts in Doc Y
        doc_x_terms = ["Acrobat Cloud Technologies", "Beacon Financial Services", "$1,250,000", "4.25%", "75 days", "King County", "Washington", "data security"]
        for term in doc_x_terms:
            self.assertNotIn(term.lower(), y_all_text.lower(), f"Doc X fact '{term}' found in Doc Y DB record!")

        # Assert zero Doc Y facts in Doc X
        doc_y_terms = ["Zenith Marine Logistics", "Apex Harbor Operators", "$840,000", "1.75%", "120 days", "Orange County", "Florida", "confidentiality"]
        for term in doc_y_terms:
            self.assertNotIn(term.lower(), x_all_text.lower(), f"Doc Y fact '{term}' found in Doc X DB record!")

    def test_api_clauses_endpoint_cross_document_isolation(self):
        """
        Validates that GET /api/documents/<doc_id>/clauses/ returns ONLY clauses belonging to that specific document.
        """
        def mock_process_doc(document_id, file_reference, user_id=None):
            if str(document_id) == str(self.doc_x.id):
                return self.doc_x_payload
            elif str(document_id) == str(self.doc_y.id):
                return self.doc_y_payload
            raise ValueError("Unknown doc")

        with patch('services.ai_client.process_document', side_effect=mock_process_doc):
            process_document(str(self.doc_x.id))
            process_document(str(self.doc_y.id))

        # API Call for Doc X
        resp_x = self.api_client.get(f'/api/documents/{self.doc_x.id}/clauses/')
        self.assertEqual(resp_x.status_code, 200)
        data_x = resp_x.json()
        clauses_resp_x = data_x.get('results') or data_x.get('clauses') or data_x
        str_x = str(clauses_resp_x).lower()

        # API Call for Doc Y
        resp_y = self.api_client.get(f'/api/documents/{self.doc_y.id}/clauses/')
        self.assertEqual(resp_y.status_code, 200)
        data_y = resp_y.json()
        clauses_resp_y = data_y.get('results') or data_y.get('clauses') or data_y
        str_y = str(clauses_resp_y).lower()

        self.assertIn("acrobat cloud technologies", str_x)
        self.assertNotIn("acrobat cloud technologies", str_y)

        self.assertIn("zenith marine logistics", str_y)
        self.assertNotIn("zenith marine logistics", str_x)
