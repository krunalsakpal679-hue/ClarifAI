"""
Comparison and ComparisonResult models matching PRD Ch. 29.6 specs.
"""
import uuid
from django.conf import settings
from django.db import models


class ComparisonStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETE = 'complete', 'Complete'
    FAILED = 'failed', 'Failed'


class ComparisonCategory(models.TextChoices):
    CHANGED = 'changed', 'Changed'
    MATCHED = 'matched', 'Matched'
    MISSING = 'missing', 'Missing'


class Comparison(models.Model):
    """
    Comparison model per PRD Ch. 29.6.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comparisons',
        db_index=True,
    )
    base_document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='base_comparisons',
        db_index=True,
    )
    target_document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_comparisons',
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=ComparisonStatus.choices,
        default=ComparisonStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comparisons'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comparison {self.id} (Base: {self.base_document_id}, Target: {self.target_document_id})"


class ComparisonResult(models.Model):
    """
    ComparisonResult model per PRD Ch. 29.6.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comparison = models.ForeignKey(
        Comparison,
        on_delete=models.CASCADE,
        related_name='results',
        db_index=True,
    )
    base_clause = models.ForeignKey(
        'documents.Clause',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='base_comparison_results',
    )
    target_clause = models.ForeignKey(
        'documents.Clause',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_comparison_results',
    )
    category = models.CharField(
        max_length=20,
        choices=ComparisonCategory.choices,
    )
    difference_explanation = models.TextField(null=True, blank=True)
    similarity_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comparison_results'
        ordering = ['created_at']

    def __str__(self):
        return f"ComparisonResult {self.id} ({self.category}) - Comp {self.comparison_id}"
