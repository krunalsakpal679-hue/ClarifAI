"""
Report model matching PRD Ch. 29.7 specs.
"""
import uuid
from django.conf import settings
from django.db import models


class ReportLanguage(models.TextChoices):
    ENGLISH = 'en', 'English'
    HINDI = 'hi', 'Hindi'


class ReportStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETE = 'complete', 'Complete'
    FAILED = 'failed', 'Failed'


class Report(models.Model):
    """
    Report model per PRD Ch. 29.7.
    Enforces validation for exactly one of (document, comparison) at serializer level.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
        db_index=True,
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        db_index=True,
    )
    comparison = models.ForeignKey(
        'comparison.Comparison',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        db_index=True,
    )
    language = models.CharField(
        max_length=10,
        choices=ReportLanguage.choices,
        default=ReportLanguage.ENGLISH,
    )
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
        db_index=True,
    )
    file_reference = models.CharField(max_length=512, null=True, blank=True)
    failure_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.id} - Status {self.status} (User {self.user_id})"
