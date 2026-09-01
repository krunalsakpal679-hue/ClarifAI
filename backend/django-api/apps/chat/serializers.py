"""
Serializers for ChatSession and ChatMessage endpoints (PRD Ch. 30.4).
"""
from rest_framework import serializers

from apps.chat.models import ChatMessage, ChatSession, MessageRole


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/documents/{id}/chat/sessions (PRD Ch. 30.4).
    """
    class Meta:
        model = ChatSession
        fields = ['id', 'document', 'title', 'created_at', 'updated_at']
        read_only_fields = ['id', 'document', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage list & detail (PRD Ch. 30.4 & Ch. 30.9).
    Exposes role, content, and source_clause_ids array.
    """
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'source_clause_ids', 'created_at']
        read_only_fields = ['id', 'role', 'content', 'source_clause_ids', 'created_at']


class ChatMessageInputSerializer(serializers.Serializer):
    """
    Serializer for POST /api/documents/{id}/chat/messages query payload.
    Accepts 'message' or 'query' field.
    """
    message = serializers.CharField(required=False, allow_blank=False)
    query = serializers.CharField(required=False, allow_blank=False)

    def validate(self, data):
        query_text = data.get('message') or data.get('query')
        if not query_text or not query_text.strip():
            raise serializers.ValidationError({"message": "Message query content cannot be empty."})
        data['query'] = query_text.strip()
        return data
