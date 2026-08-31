"""
Phase 8 Risk Classification, Rule Engine Persistence & Async Pipeline Integration Tests:
- Full pipeline execution & persistence against MockAIClient (summary + clauses + rule_findings)
- Per-clause failure isolation (Ch. 16.5)
- Part B.6 conflict policy (classifier severity wins, rule findings preserved as evidence)
- Invalid classifier output protection (Ch. 56.10, never silently converted to "Safe")
- Idempotency & duplicate cleanup on re-execution
- Top-level AI adapter failure transitions Document to FAILED with failure_reason
"""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.documents.models import (
    Clause,
    ClauseStatus,
    Document,
    DocumentStatus,
    DocumentSummary,
)
from services.ai_client.exceptions import AIServiceRateLimitError
from services.ai_client.mock import MockAIClient
from tasks.document_tasks import process_document

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=True,
)
class RiskPipelineTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='pipelinetest@example.com',
            password='Password123!'
        )
        self.doc = Document.objects.create(
            user=self.user,
            original_filename='commercial_agreement.pdf',
            file_reference='uploads/documents/commercial_agreement.pdf',
            status=DocumentStatus.QUEUED
        )

    def test_full_pipeline_happy_path_persistence(self):
        """Full pipeline execution against MockAIClient creates DocumentSummary, Clauses, and rule_findings."""
        result = process_document(str(self.doc.id))
        self.assertEqual(result['status'], 'complete')

        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.COMPLETE)

        # 1. DocumentSummary created
        summary = DocumentSummary.objects.get(document=self.doc)
        self.assertIn("Standard commercial agreement", summary.purpose_text)
        self.assertIn("Net 30 payment terms", summary.key_risks_text)

        # 2. Clauses & rule_findings created
        clauses = Clause.objects.filter(document=self.doc).order_by('position')
        self.assertEqual(clauses.count(), 4)

        c1 = clauses[0]  # Liability clause
        self.assertEqual(c1.severity, 'high')
        self.assertEqual(c1.category, 'Liability')
        self.assertEqual(c1.status, ClauseStatus.COMPLETE)
        self.assertEqual(len(c1.rule_findings), 1)
        self.assertEqual(c1.rule_findings[0]['rule_id'], 'R-101')

        c2 = clauses[1]  # Payment clause
        self.assertEqual(c2.severity, 'moderate')
        self.assertEqual(c2.category, 'Payment')
        self.assertEqual(c2.status, ClauseStatus.COMPLETE)
        self.assertEqual(len(c2.rule_findings), 1)
        self.assertEqual(c2.rule_findings[0]['rule_id'], 'R-202')

        c3 = clauses[2]  # Confidentiality clause
        self.assertEqual(c3.severity, 'safe')
        self.assertEqual(c3.category, 'Confidentiality')
        self.assertEqual(c3.status, ClauseStatus.COMPLETE)
        self.assertEqual(len(c3.rule_findings), 0)

    def test_per_clause_failure_isolation(self):
        """Per-clause failure isolation (Ch. 16.5): failed clause is marked ClauseStatus.FAILED, while valid clauses succeed."""
        process_document(str(self.doc.id))
        clauses = Clause.objects.filter(document=self.doc).order_by('position')

        # Clause 4 (c-004) is the per-clause failure example
        c4 = clauses[3]
        self.assertEqual(c4.position, 4)
        self.assertEqual(c4.status, ClauseStatus.FAILED)
        self.assertIsNone(c4.severity)  # Never invent severity for failed clause
        self.assertIsNone(c4.category)
        self.assertIn("Processing failed for this specific clause segment", c4.simplified_text)


        # First 3 clauses are valid and complete
        for idx in range(3):
            self.assertEqual(clauses[idx].status, ClauseStatus.COMPLETE)
            self.assertIsNotNone(clauses[idx].severity)

    def test_rule_classifier_conflict_policy(self):
        """Part B.6 Conflict Policy: Classifier severity is stored as definitive; rule finding is preserved as evidence."""
        # Custom mock payload where rule finding score is high (0.95), but classifier output is 'moderate'
        conflict_payload = {
            "document_id": str(self.doc.id),
            "summary": {"overview": "Conflict test agreement", "key_points": []},
            "clauses": [
                {
                    "clause_id": "c-conflict",
                    "severity": "moderate",  # Classifier says moderate
                    "category": "Payment",
                    "original_text": "Late payment fee of 2% per month applies.",
                    "simplified_text": "Late fee is 2% monthly.",
                    "explanation": "Classifier evaluated moderate risk.",
                    "rule_findings": [{"rule_id": "R-001", "risk_score": 0.95, "matched_pattern": "late fee > 1.5%"}],
                    "status": "success"
                }
            ]
        }

        with patch("services.ai_client.process_document", return_value=conflict_payload):
            process_document(str(self.doc.id))

        clause = Clause.objects.get(document=self.doc)
        # Classifier severity is final
        self.assertEqual(clause.severity, 'moderate')
        self.assertNotEqual(clause.severity, 'high')

        # Rule finding preserved as evidence
        self.assertEqual(len(clause.rule_findings), 1)
        self.assertEqual(clause.rule_findings[0]['rule_id'], 'R-001')
        self.assertEqual(clause.rule_findings[0]['risk_score'], 0.95)

    def test_invalid_classifier_output_never_becomes_safe(self):
        """Ch. 56.10 Prohibition: Invalid classifier output results in ClauseStatus.FAILED, NEVER silently converted to 'safe'."""
        invalid_payload = {
            "document_id": str(self.doc.id),
            "summary": {"overview": "Invalid classifier output test", "key_points": []},
            "clauses": [
                {
                    "clause_id": "c-invalid",
                    "severity": "UNKNOWN_SEVERITY_LEVEL",  # Invalid severity
                    "category": "Payment",
                    "original_text": "Some text",
                    "simplified_text": "Simplified text",
                    "explanation": "Explanation",
                    "rule_findings": [],
                    "status": "success"
                }
            ]
        }

        with patch("services.ai_client.process_document", return_value=invalid_payload):
            process_document(str(self.doc.id))

        clause = Clause.objects.get(document=self.doc)
        self.assertEqual(clause.status, ClauseStatus.FAILED)
        self.assertIsNone(clause.severity)
        self.assertNotEqual(clause.severity, 'safe')  # Explicitly assert NOT converted to safe

    def test_pipeline_idempotency_cleanup(self):
        """Reprocessing a document clears prior clauses/summary records to prevent duplicates."""
        # First execution
        process_document(str(self.doc.id))
        self.assertEqual(Clause.objects.filter(document=self.doc).count(), 4)
        self.assertEqual(DocumentSummary.objects.filter(document=self.doc).count(), 1)

        # Reset document status to QUEUED for reprocessing test
        self.doc.status = DocumentStatus.QUEUED
        self.doc.save()

        # Second execution
        process_document(str(self.doc.id))

        # Counts must remain identical (not duplicated)
        self.assertEqual(Clause.objects.filter(document=self.doc).count(), 4)
        self.assertEqual(DocumentSummary.objects.filter(document=self.doc).count(), 1)

    def test_ai_adapter_failure_transitions_document_to_failed(self):
        """Top-level AI adapter failure (e.g. rate limit) transitions Document to FAILED with failure_reason."""
        with patch("services.ai_client.process_document", side_effect=AIServiceRateLimitError("429 Quota Exhausted")):
            with self.assertRaises(AIServiceRateLimitError):
                process_document(str(self.doc.id))

        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.FAILED)
        self.assertIn("429 Quota Exhausted", self.doc.failure_reason)
