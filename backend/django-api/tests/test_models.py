"""
Phase 4 Domain Model Unit Tests:
- Verifies creation & constraints for all 9 database tables from PRD Ch. 29
- Validates 4-value Severity Enum, fixed 8-category Category Enum, and Document Status Enums
- Validates Rule Findings JSONField on Clause
- Validates Foreign Key relationships & indexing
"""
import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.documents.models import (
    Document, DocumentStatus,
    Clause, ClauseSeverity, ClauseCategory, ClauseStatus,
    DocumentSummary,
)
from apps.chat.models import ChatSession, ChatMessage, MessageRole
from apps.comparison.models import Comparison, ComparisonStatus, ComparisonResult, ComparisonCategory
from apps.reports.models import Report, ReportLanguage
from apps.audit.models import AuditLog

User = get_user_model()


class DomainModelsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='modeltest@example.com',
            password='Password123!'
        )

    def test_document_model_creation_and_enums(self):
        """Test Document model creation with valid DocumentStatus choices."""
        doc = Document.objects.create(
            user=self.user,
            original_filename='employment_agreement.pdf',
            file_reference='uploads/2026/08/employment_agreement.pdf',
            document_type='Employment Contract',
            status=DocumentStatus.QUEUED
        )
        self.assertIsInstance(doc.id, uuid.UUID)
        self.assertEqual(doc.status, 'queued')
        self.assertEqual(doc.user, self.user)

        # Test updating status through processing states
        doc.status = DocumentStatus.EXTRACTING
        doc.save()
        self.assertEqual(doc.status, 'extracting')

    def test_clause_model_severity_and_category_enums(self):
        """Test Clause model creation and enforcement of 4-value Severity and fixed 8-category Enums."""
        doc = Document.objects.create(
            user=self.user,
            original_filename='contract.pdf',
            file_reference='uploads/contract.pdf'
        )

        clause = Clause.objects.create(
            document=doc,
            position=1,
            original_text='Either party may terminate this agreement upon 30 days written notice.',
            simplified_text='Either party can end this contract with a 30-day written notice.',
            severity=ClauseSeverity.HIGH,
            category=ClauseCategory.TERMINATION,
            explanation='Allows unilateral termination.',
            status=ClauseStatus.COMPLETE,
            rule_findings=[{
                "rule_id": "RULE-TERM-01",
                "risk_signal": "unilateral_termination",
                "matched_text": "terminate this agreement",
                "clause_id": str(uuid.uuid4()),
                "evidence": "Clause allows 30 days notice",
                "rule_version": "1.0.0"
            }]
        )
        self.assertIsInstance(clause.id, uuid.UUID)
        self.assertEqual(clause.severity, 'high')
        self.assertEqual(clause.category, 'Termination')
        self.assertEqual(len(clause.rule_findings), 1)

        # Test invalid severity enum rejection
        invalid_clause = Clause(
            document=doc,
            position=2,
            original_text='Text',
            severity='extreme_high',  # Invalid enum value
            category=ClauseCategory.PAYMENT
        )
        with self.assertRaises(ValidationError):
            invalid_clause.full_clean()

        # Test invalid category enum rejection
        invalid_cat_clause = Clause(
            document=doc,
            position=3,
            original_text='Text',
            severity=ClauseSeverity.SAFE,
            category='UnapprovedCategoryName'  # Invalid category
        )
        with self.assertRaises(ValidationError):
            invalid_cat_clause.full_clean()

    def test_document_summary_one_to_one_relationship(self):
        """Test DocumentSummary 1:1 relationship with Document."""
        doc = Document.objects.create(
            user=self.user,
            original_filename='summary_test.pdf',
            file_reference='uploads/summary_test.pdf'
        )
        summary = DocumentSummary.objects.create(
            document=doc,
            purpose_text='General service agreement',
            obligations_text='Vendor must deliver services monthly.',
            key_terms_text='Net 30 payment terms.',
            key_risks_text='High liability exposure.'
        )
        self.assertEqual(summary.document, doc)
        self.assertEqual(doc.summary, summary)

    def test_chat_session_and_message_models(self):
        """Test ChatSession and ChatMessage model creation."""
        doc = Document.objects.create(
            user=self.user,
            original_filename='chat_doc.pdf',
            file_reference='uploads/chat_doc.pdf'
        )
        session = ChatSession.objects.create(
            user=self.user,
            document=doc,
            title='Contract Clarification Chat'
        )
        self.assertIsInstance(session.id, uuid.UUID)

        msg = ChatMessage.objects.create(
            session=session,
            role=MessageRole.USER,
            content='What is the notice period for termination?',
            source_clause_ids=[str(uuid.uuid4())]
        )
        self.assertIsInstance(msg.id, uuid.UUID)
        self.assertEqual(msg.role, 'user')
        self.assertEqual(len(msg.source_clause_ids), 1)

    def test_comparison_and_comparison_result_models(self):
        """Test Comparison and ComparisonResult models."""
        doc_base = Document.objects.create(
            user=self.user,
            original_filename='v1.pdf',
            file_reference='uploads/v1.pdf'
        )
        doc_target = Document.objects.create(
            user=self.user,
            original_filename='v2.pdf',
            file_reference='uploads/v2.pdf'
        )

        comp = Comparison.objects.create(
            user=self.user,
            base_document=doc_base,
            target_document=doc_target,
            status=ComparisonStatus.COMPLETE
        )
        self.assertIsInstance(comp.id, uuid.UUID)

        result = ComparisonResult.objects.create(
            comparison=comp,
            category=ComparisonCategory.CHANGED,
            difference_explanation='Termination notice changed from 30 to 60 days.',
            similarity_score=0.85
        )
        self.assertEqual(result.category, 'changed')
        self.assertEqual(result.similarity_score, 0.85)

    def test_report_model(self):
        """Test Report model creation and language enum."""
        doc = Document.objects.create(
            user=self.user,
            original_filename='report_doc.pdf',
            file_reference='uploads/report_doc.pdf'
        )
        report = Report.objects.create(
            user=self.user,
            document=doc,
            language=ReportLanguage.HINDI,
            file_reference='exports/reports/report_hi.pdf'
        )
        self.assertIsInstance(report.id, uuid.UUID)
        self.assertEqual(report.language, 'hi')

    def test_audit_log_model_security_and_nullable_user(self):
        """Test AuditLog model with authenticated and anonymous/pre-auth events."""
        # Authenticated audit log
        log_auth = AuditLog.objects.create(
            user=self.user,
            event_type='DOCUMENT_UPLOADED',
            metadata={'filename': 'contract.pdf', 'file_size_bytes': 1048576}
        )
        self.assertIsInstance(log_auth.id, uuid.UUID)
        self.assertEqual(log_auth.user, self.user)

        # Pre-auth / Anonymous audit log (e.g. failed login attempt)
        log_anon = AuditLog.objects.create(
            user=None,
            event_type='FAILED_LOGIN_ATTEMPT',
            metadata={'ip_address': '127.0.0.1', 'email_attempted': 'unknown@example.com'}
        )
        self.assertIsNone(log_anon.user)
        self.assertEqual(log_anon.event_type, 'FAILED_LOGIN_ATTEMPT')
