"""
URL routing for Chat endpoints (PRD Ch. 30.4).
Nested under /api/documents/<uuid:pk>/chat/
"""
from django.urls import path
from apps.chat.views import (
    ChatMessageListCreateView,
    ChatSessionGetOrCreateView,
)

urlpatterns = [
    path('sessions/', ChatSessionGetOrCreateView.as_view(), name='document_chat_sessions'),
    path('messages/', ChatMessageListCreateView.as_view(), name='document_chat_messages'),
]
