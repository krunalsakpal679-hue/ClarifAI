"""
Report model matching PRD Ch. 29.7 specs.
"""
import uuid
from django.conf import settings
from django.db import models


class ReportLanguage(models.TextChoices):
    ENGLISH = 'en', 'English'
    HINDI = 'hi', 'Hindi'


class Report(models.Model):
    """
    Report model per PRD Ch. 29.7.
    Note: Validation enforcing exactly one of (document, comparison) is handled at the serializer level per Task 7.
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
    file_reference = models.CharField(max_length=512, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.id} - Lang {self.language} (User {self.user_id})"
