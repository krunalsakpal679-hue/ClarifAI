"""
Documents, Clauses, and DocumentSummaries models matching PRD Ch. 29.2, 29.3, 29.4 specs.
"""
import uuid
from django.conf import settings
from django.db import models


class DocumentStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    EXTRACTING = 'extracting', 'Extracting'
    OCR = 'ocr', 'OCR Processing'
    SEGMENTING = 'segmenting', 'Segmenting'
    CLASSIFYING = 'classifying', 'Classifying'
    SIMPLIFYING = 'simplifying', 'Simplifying'
    SUMMARIZING = 'summarizing', 'Summarizing'
    INDEXING = 'indexing', 'Indexing'
    COMPLETE = 'complete', 'Complete'
    FAILED = 'failed', 'Failed'


class ClauseSeverity(models.TextChoices):
    HIGH = 'high', 'High'
    MODERATE = 'moderate', 'Moderate'
    LOW = 'low', 'Low'
    SAFE = 'safe', 'Safe'


class ClauseCategory(models.TextChoices):
    PAYMENT = 'Payment', 'Payment'
    TERMINATION = 'Termination', 'Termination'
    RENEWAL = 'Renewal', 'Renewal'
    CONFIDENTIALITY = 'Confidentiality', 'Confidentiality'
    LIABILITY = 'Liability', 'Liability'
    INTELLECTUAL_PROPERTY = 'Intellectual Property', 'Intellectual Property'
    PRIVACY = 'Privacy', 'Privacy'
    DISPUTE_RESOLUTION = 'Dispute Resolution', 'Dispute Resolution'


class ClauseStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETE = 'complete', 'Complete'
    FAILED = 'failed', 'Failed'


# Valid forward state transitions graph per PRD Ch. 15
DOCUMENT_VALID_TRANSITIONS = {
    DocumentStatus.QUEUED: [DocumentStatus.EXTRACTING, DocumentStatus.FAILED],
    DocumentStatus.EXTRACTING: [DocumentStatus.OCR, DocumentStatus.FAILED],
    DocumentStatus.OCR: [DocumentStatus.SEGMENTING, DocumentStatus.FAILED],
    DocumentStatus.SEGMENTING: [DocumentStatus.CLASSIFYING, DocumentStatus.FAILED],
    DocumentStatus.CLASSIFYING: [DocumentStatus.SIMPLIFYING, DocumentStatus.FAILED],
    DocumentStatus.SIMPLIFYING: [DocumentStatus.SUMMARIZING, DocumentStatus.FAILED],
    DocumentStatus.SUMMARIZING: [DocumentStatus.INDEXING, DocumentStatus.FAILED],
    DocumentStatus.INDEXING: [DocumentStatus.COMPLETE, DocumentStatus.FAILED],
    DocumentStatus.COMPLETE: [],
    DocumentStatus.FAILED: [],
}


class Document(models.Model):
    """
    Document model per PRD Ch. 29.2 & Ch. 15 status state machine.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True,
    )
    original_filename = models.CharField(max_length=255)
    file_reference = models.CharField(max_length=512)
    document_type = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=DocumentStatus.choices,
        default=DocumentStatus.QUEUED,
        db_index=True,
    )
    failure_reason = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename} ({self.status})"

    def transition_to(self, new_status, failure_reason=None):
        """
        Transitions document processing status following PRD Ch. 15 state machine rules.
        Rejects invalid, out-of-order, or post-terminal transitions with ValueError.
        """
        if self.status == new_status:
            return  # Idempotent no-op

        if new_status == DocumentStatus.FAILED:
            self.status = DocumentStatus.FAILED
            if failure_reason:
                self.failure_reason = str(failure_reason)
            self.save(update_fields=['status', 'failure_reason', 'updated_at'])
            return

        allowed_next = DOCUMENT_VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed_next:
            raise ValueError(
                f"Invalid status transition from '{self.status}' to '{new_status}'. Allowed: {allowed_next}"
            )

        self.status = new_status
        self.save(update_fields=['status', 'updated_at'])



class Clause(models.Model):
    """
    Clause model per PRD Ch. 29.3 & Rule-Findings schema decision (Ch. 29.10).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='clauses',
        db_index=True,
    )
    position = models.IntegerField()
    original_text = models.TextField()
    simplified_text = models.TextField(null=True, blank=True)
    severity = models.CharField(
        max_length=20,
        choices=ClauseSeverity.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    category = models.CharField(
        max_length=50,
        choices=ClauseCategory.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    explanation = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ClauseStatus.choices,
        default=ClauseStatus.PENDING,
    )
    # Rule findings stored as embedded JSON array per Ch. 29.10 decision
    rule_findings = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clauses'
        ordering = ['position']

    def __str__(self):
        return f"Clause {self.position} - Doc {self.document_id}"


class DocumentSummary(models.Model):
    """
    DocumentSummary model per PRD Ch. 29.4 (1:1 with Document).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='summary',
        db_index=True,
    )
    purpose_text = models.TextField(null=True, blank=True)
    obligations_text = models.TextField(null=True, blank=True)
    key_terms_text = models.TextField(null=True, blank=True)
    key_risks_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_summaries'

    def __str__(self):
        return f"Summary for Doc {self.document_id}"
