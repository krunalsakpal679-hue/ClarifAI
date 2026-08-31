"""
ChatSession and ChatMessage models matching PRD Ch. 29.5 specs.
"""
import uuid
from django.conf import settings
from django.db import models


class MessageRole(models.TextChoices):
    USER = 'user', 'User'
    ASSISTANT = 'assistant', 'Assistant'
    SYSTEM = 'system', 'System'


class ChatSession(models.Model):
    """
    ChatSession model per PRD Ch. 29.5.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
        db_index=True,
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
        db_index=True,
    )
    title = models.CharField(max_length=255, default='New Chat Session')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return f"ChatSession {self.id} - User {self.user_id}"


class ChatMessage(models.Model):
    """
    ChatMessage model per PRD Ch. 29.5 with source_clause_ids array.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True,
    )
    role = models.CharField(max_length=20, choices=MessageRole.choices)
    content = models.TextField()
    source_clause_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message {self.id} ({self.role}) - Session {self.session_id}"
