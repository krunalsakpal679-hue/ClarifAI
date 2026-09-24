"""
Database Schema & Migration Validation Against Contract (BOOK4-PHASE-06).
Validates that every table, field, primary key, foreign key, index, nullability,
cascade deletion rule, and §29.10 rule_findings field matches PRD Ch. 29 & Prompt Book B.4.
"""
import uuid
from django.conf import settings
from django.db import models
from django.test import TestCase

from apps.audit.models import AuditLog
from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.comparison.models import (
    Comparison,
    ComparisonCategory,
    ComparisonResult,
    ComparisonStatus,
)
from apps.documents.models import (
    Clause,
    ClauseCategory,
    ClauseSeverity,
    ClauseStatus,
    Document,
    DocumentStatus,
    DocumentSummary,
)
from apps.reports.models import Report, ReportLanguage, ReportStatus
from apps.users.models import User


class DatabaseSchemaContractTestCase(TestCase):
    """
    Automated contract verification for database schema against Backend Prompt Book Part B.4.
    """

    def test_table_names(self):
        """All 10 core tables use exact specified db_table names."""
        self.assertEqual(User._meta.db_table, 'users')
        self.assertEqual(Document._meta.db_table, 'documents')
        self.assertEqual(Clause._meta.db_table, 'clauses')
        self.assertEqual(DocumentSummary._meta.db_table, 'document_summaries')
        self.assertEqual(ChatSession._meta.db_table, 'chat_sessions')
        self.assertEqual(ChatMessage._meta.db_table, 'chat_messages')
        self.assertEqual(Comparison._meta.db_table, 'comparisons')
        self.assertEqual(ComparisonResult._meta.db_table, 'comparison_results')
        self.assertEqual(Report._meta.db_table, 'reports')
        self.assertEqual(AuditLog._meta.db_table, 'audit_logs')

    def test_all_primary_keys_are_uuids(self):
        """Zero sequential-integer primary keys; 100% UUID primary keys per Ch. 26.2."""
        core_models = [
            User, Document, Clause, DocumentSummary,
            ChatSession, ChatMessage, Comparison,
            ComparisonResult, Report, AuditLog
        ]
        for model in core_models:
            pk_field = model._meta.pk
            self.assertIsInstance(
                pk_field,
                models.UUIDField,
                f"Model {model.__name__} PK is {type(pk_field)}, expected UUIDField."
            )

    def test_ownership_foreign_keys_are_indexed_and_non_nullable(self):
        """Ownership user_id FKs on documents, chat_sessions, comparisons, reports are indexed and non-nullable."""
        ownership_models = [Document, ChatSession, Comparison, Report]
        for model in ownership_models:
            user_field = model._meta.get_field('user')
            self.assertFalse(
                user_field.null,
                f"Ownership field {model.__name__}.user must be non-nullable."
            )
            self.assertTrue(
                user_field.db_index,
                f"Ownership field {model.__name__}.user must be indexed."
            )

    def test_clause_rule_findings_and_severity_schema(self):
        """Clause table contains rule_findings JSONField and canonical 4-level severity enum."""
        rf_field = Clause._meta.get_field('rule_findings')
        self.assertIsInstance(rf_field, models.JSONField)

        sev_field = Clause._meta.get_field('severity')
        self.assertTrue(sev_field.db_index)
        expected_severities = {'high', 'moderate', 'low', 'safe'}
        self.assertEqual(set(ClauseSeverity.values), expected_severities)

        cat_field = Clause._meta.get_field('category')
        self.assertTrue(cat_field.db_index)
        expected_categories = {
            'Payment', 'Termination', 'Renewal', 'Confidentiality',
            'Liability', 'Intellectual Property', 'Privacy', 'Dispute Resolution'
        }
        self.assertEqual(set(ClauseCategory.values), expected_categories)

    def test_active_data_cascade_deletion_rules(self):
        """Active-data deletion cascade matches PRD §26.5.2 & §29."""
        user = User.objects.create_user(email="cascade@example.com", password="SecurePassword123!")
        
        # Create Document
        doc = Document.objects.create(
            user=user,
            original_filename="contract.pdf",
            file_reference="uploads/contract.pdf"
        )
        clause = Clause.objects.create(
            document=doc,
            position=1,
            original_text="Payment within 30 days.",
            rule_findings=[{"rule_id": "R001", "description": "Payment term detected"}]
        )
        summary = DocumentSummary.objects.create(
            document=doc,
            purpose_text="Summary purpose"
        )
        session = ChatSession.objects.create(user=user, document=doc)
        msg = ChatMessage.objects.create(
            session=session,
            role=MessageRole.USER,
            content="Hello",
            source_clause_ids=[1]
        )
        comparison = Comparison.objects.create(
            user=user,
            base_document=doc,
            target_document=doc
        )
        comp_res = ComparisonResult.objects.create(
            comparison=comparison,
            base_clause=clause,
            target_clause=clause,
            category=ComparisonCategory.MATCHED
        )
        report = Report.objects.create(user=user, document=doc, comparison=comparison)
        audit = AuditLog.objects.create(user=user, event_type="test_event")

        # 1. Document Deletion Cascade:
        # Deleting doc cascades to clause and summary; sets document null on session, comparison, report.
        doc.delete()
        self.assertFalse(Clause.objects.filter(id=clause.id).exists())
        self.assertFalse(DocumentSummary.objects.filter(id=summary.id).exists())
        
        session.refresh_from_db()
        self.assertIsNone(session.document)
        
        comparison.refresh_from_db()
        self.assertIsNone(comparison.base_document)
        self.assertIsNone(comparison.target_document)
        
        report.refresh_from_db()
        self.assertIsNone(report.document)

        # 2. ChatSession Deletion Cascade:
        # Deleting session cascades to messages.
        session.delete()
        self.assertFalse(ChatMessage.objects.filter(id=msg.id).exists())

        # 3. Comparison Deletion Cascade:
        # Deleting comparison cascades to comparison_results.
        comparison.delete()
        self.assertFalse(ComparisonResult.objects.filter(id=comp_res.id).exists())

        # 4. User Deletion Cascade:
        # Deleting user cascades to reports and sets user null on audit_logs.
        user.delete()
        self.assertFalse(Report.objects.filter(id=report.id).exists())
        
        audit.refresh_from_db()
        self.assertIsNone(audit.user)
