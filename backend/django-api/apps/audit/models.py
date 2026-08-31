"""
AuditLog model matching PRD Ch. 29.8 specs.
"""
import uuid
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    AuditLog model per PRD Ch. 29.8.
    Security Constraint (Ch. 26.8 & Ch. 31): metadata MUST NEVER store plain passwords,
    tokens, authentication secrets, or raw confidential contract text.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        db_index=True,
    )
    event_type = models.CharField(max_length=100, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        user_repr = self.user_id if self.user_id else 'Anonymous/System'
        return f"AuditLog [{self.event_type}] - User {user_repr} at {self.created_at}"
