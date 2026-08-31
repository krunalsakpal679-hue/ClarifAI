"""
Views for ChatSession and ChatMessage endpoints (PRD Ch. 30.4 & Part B.7).
Enforces session-scoped, document-scoped memory (one continuous session per user per document).
"""
import logging
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.chat.serializers import (
    ChatMessageInputSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
)
from apps.documents.models import Document, DocumentStatus
from apps.documents.views import DocumentNotReadyException
from core.pagination import StandardPageNumberPagination
from core.permissions import IsOwner
from services import ai_client
from services.ai_client.exceptions import AIServiceError

logger = logging.getLogger(__name__)

HISTORY_WINDOW_SIZE = 10  # Engineering Implementation Detail (Classification E)


class ChatSessionGetOrCreateView(generics.RetrieveAPIView):
    """
    GET /api/documents/{id}/chat/sessions - Get or create unique chat session for (user, document) pair.
    PRD Ch. 17.10: One continuous session per document per user.
    """
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ChatSessionSerializer

    def get_object(self):
        document_id = self.kwargs.get('pk')
        document = get_object_or_404(Document, pk=document_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(self.request, document)

        session, _ = ChatSession.objects.get_or_create(
            user=self.request.user,
            document=document,
            defaults={'title': f"Chat on {document.original_filename}"}
        )
        return session


class AIChatServiceUnavailableException(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'AI chat service currently unavailable. Your message was saved.'
    default_code = 'AI_SERVICE_UNAVAILABLE'


class ChatMessageListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/documents/{id}/chat/messages - Full ordered session message history (Owner-only).
    POST /api/documents/{id}/chat/messages - Send query to chatbot (Owner-only).
    
    Security & Scope Rules (Part B.7, Ch. 17.10, Ch. 30.4, Ch. 30.9):
    - Document Status: Must be DocumentStatus.COMPLETE (returns 422 DOCUMENT_NOT_READY if incomplete).
    - Ownership: Strictly scoped to document owner (returns 404 for non-owners).
    - Prompt Injection Defense: Query and history passed as plain JSON data fields.
    - User Message Protection: User message is persisted BEFORE calling AI adapter. If AI fails, user message is retained.
    - No-Answer Handling: Controlled no-answer response persisted as normal message (never HTTP error).
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatMessageInputSerializer
        return ChatMessageSerializer

    def get_queryset(self):
        document_id = self.kwargs.get('pk')
        document = get_object_or_404(Document, pk=document_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(self.request, document)

        session, _ = ChatSession.objects.get_or_create(
            user=self.request.user,
            document=document,
            defaults={'title': f"Chat on {document.original_filename}"}
        )

        return session.messages.all().order_by('created_at')

    def create(self, request, *args, **kwargs):
        document_id = self.kwargs.get('pk')
        document = get_object_or_404(Document, pk=document_id)

        # Enforce IsOwner 404-not-403 policy
        self.check_object_permissions(request, document)

        if document.status != DocumentStatus.COMPLETE:
            raise DocumentNotReadyException()

        input_serializer = ChatMessageInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        query_text = input_serializer.validated_data['query']

        # Get or create unique session for this (user, document) pair
        session, _ = ChatSession.objects.get_or_create(
            user=request.user,
            document=document,
            defaults={'title': f"Chat on {document.original_filename}"}
        )

        # 1. Persist User Message FIRST (guarantees user input is never lost)
        user_message = ChatMessage.objects.create(
            session=session,
            role=MessageRole.USER,
            content=query_text,
            source_clause_ids=[]
        )

        # 2. Gather Recent Conversation History Window (10 messages, strictly within this session)
        history_qs = session.messages.filter(
            created_at__lt=user_message.created_at
        ).order_by('-created_at')[:HISTORY_WINDOW_SIZE]

        history_list = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(list(history_qs))
        ]

        # 3. Forward to AI Client Adapter
        try:
            ai_response = ai_client.chat(
                document_id=str(document.id),
                message=query_text,
                history=history_list
            )
        except AIServiceError as exc:
            logger.error(f"AI chat client error for document {document.id}: {exc}")
            # Retain user_message in database; raise 503 chat error response
            raise AIChatServiceUnavailableException()

        # 4. Persist Assistant Answer (including no-answer legal framing as normal message)
        answer_text = ai_response.get('answer', '')
        source_clause_ids = ai_response.get('source_clause_ids', [])

        assistant_message = ChatMessage.objects.create(
            session=session,
            role=MessageRole.ASSISTANT,
            content=answer_text,
            source_clause_ids=source_clause_ids if isinstance(source_clause_ids, list) else []
        )

        # Update session timestamp
        session.save(update_fields=['updated_at'])

        response_serializer = ChatMessageSerializer(assistant_message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


