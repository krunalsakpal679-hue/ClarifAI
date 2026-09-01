"""
Phase 10 AI Chatbot Microservice Integration & Backend Query Endpoints Tests:
- GET /api/documents/{id}/chat/sessions (get-or-create session per user per document)
- POST /api/documents/{id}/chat/messages (send message, 10-message history window forwarding, persistence)
- GET /api/documents/{id}/chat/messages (ordered history list)
- Incomplete document protection (422 DOCUMENT_NOT_READY)
- User message retention on AI failure (user message preserved when AI call fails)
- Controlled no-answer response handling (persisted as normal message, not error)
- Cross-user and cross-document isolation tests (Ch. 17.4 & Part B.7)
"""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.documents.models import Document, DocumentStatus
from services.ai_client.exceptions import AIServiceUnavailableError

User = get_user_model()


class ChatEndpointsTestCase(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            email='usera@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='userb@example.com',
            password='Password123!'
        )

        # Completed document owned by User A
        self.doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='usera_agreement.pdf',
            file_reference='uploads/documents/usera_agreement.pdf',
            status=DocumentStatus.COMPLETE
        )

        # Completed document owned by User B
        self.doc_b = Document.objects.create(
            user=self.user_b,
            original_filename='userb_agreement.pdf',
            file_reference='uploads/documents/userb_agreement.pdf',
            status=DocumentStatus.COMPLETE
        )

        # Incomplete document owned by User A
        self.incomplete_doc_a = Document.objects.create(
            user=self.user_a,
            original_filename='usera_processing.pdf',
            file_reference='uploads/documents/usera_processing.pdf',
            status=DocumentStatus.EXTRACTING
        )

    def test_get_or_create_chat_session(self):
        """GET /api/documents/{id}/chat/sessions get-or-creates unique session for (user, document)."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_chat_sessions', kwargs={'pk': self.doc_a.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['document']), str(self.doc_a.id))

        # Check DB session count
        self.assertEqual(ChatSession.objects.filter(user=self.user_a, document=self.doc_a).count(), 1)

        # Second call returns same session
        response2 = self.client.get(url)
        self.assertEqual(response2.data['id'], response.data['id'])

    def test_send_chat_message_success(self):
        """POST /api/documents/{id}/chat/messages persists user message, calls AI adapter, and returns assistant message."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_chat_messages', kwargs={'pk': self.doc_a.id})
        payload = {"message": "What are the payment terms in this agreement?"}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'assistant')
        self.assertIn("Net 30 payment terms", response.data['content'])

        # Verify DB messages (1 user, 1 assistant)
        session = ChatSession.objects.get(user=self.user_a, document=self.doc_a)
        messages = session.messages.all().order_by('created_at')
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].role, MessageRole.USER)
        self.assertEqual(messages[0].content, payload["message"])
        self.assertEqual(messages[1].role, MessageRole.ASSISTANT)

    def test_send_chat_message_incomplete_returns_422(self):
        """POST /api/documents/{id}/chat/messages on incomplete document returns HTTP 422 DOCUMENT_NOT_READY."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_chat_messages', kwargs={'pk': self.incomplete_doc_a.id})
        payload = {"message": "Can I chat about this document?"}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['error']['code'], 'DOCUMENT_NOT_READY')

    def test_send_chat_message_non_owned_returns_404(self):
        """POST /api/documents/{id}/chat/messages on non-owned document returns 404 Not Found."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_chat_messages', kwargs={'pk': self.doc_b.id})
        payload = {"message": "Trying to read User B's document."}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ai_failure_retains_user_message(self):
        """Simulated AI adapter failure returns 503 error, but user message remains saved in database."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_chat_messages', kwargs={'pk': self.doc_a.id})
        payload = {"message": "Message that triggers AI service failure."}

        with patch("services.ai_client.chat", side_effect=AIServiceUnavailableError("AI server down")):
            response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['error']['code'], 'AI_SERVICE_UNAVAILABLE')

        # User message MUST remain saved in database
        session = ChatSession.objects.get(user=self.user_a, document=self.doc_a)
        messages = session.messages.all()
        self.assertEqual(messages.count(), 1)
        self.assertEqual(messages[0].role, MessageRole.USER)
        self.assertEqual(messages[0].content, payload["message"])

    def test_no_answer_response_handling(self):
        """Controlled no-answer response is persisted and returned as a normal message (never HTTP error)."""
        no_answer_payload = {
            "answer": "This agreement does not contain information regarding termination fees. Note: This does NOT constitute legal advice.",
            "source_clause_ids": []
        }
        self.client.force_authenticate(user=self.user_a)
        url = reverse('document_chat_messages', kwargs={'pk': self.doc_a.id})

        with patch("services.ai_client.chat", return_value=no_answer_payload):
            response = self.client.post(url, {"message": "What is the penalty for early termination?"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'assistant')
        self.assertIn("does not contain information", response.data['content'])
        self.assertEqual(response.data['source_clause_ids'], [])

    def test_chat_messages_ordered_history(self):
        """GET /api/documents/{id}/chat/messages returns messages in chronological order."""
        self.client.force_authenticate(user=self.user_a)
        session = ChatSession.objects.create(user=self.user_a, document=self.doc_a)
        ChatMessage.objects.create(session=session, role=MessageRole.USER, content="Hello")
        ChatMessage.objects.create(session=session, role=MessageRole.ASSISTANT, content="Hi there!")

        url = reverse('document_chat_messages', kwargs={'pk': self.doc_a.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['role'], 'user')
        self.assertEqual(results[1]['role'], 'assistant')

    def test_cross_user_isolation(self):
        """Critical Security (Ch. 17.4): User A cannot read or send messages in User B's document session."""
        session_b = ChatSession.objects.create(user=self.user_b, document=self.doc_b)
        ChatMessage.objects.create(session=session_b, role=MessageRole.USER, content="User B confidential query")

        # User A attempts GET sessions on User B's doc
        self.client.force_authenticate(user=self.user_a)
        url_sessions = reverse('document_chat_sessions', kwargs={'pk': self.doc_b.id})
        res_sessions = self.client.get(url_sessions)
        self.assertEqual(res_sessions.status_code, status.HTTP_404_NOT_FOUND)

        # User A attempts GET messages on User B's doc
        url_messages = reverse('document_chat_messages', kwargs={'pk': self.doc_b.id})
        res_messages = self.client.get(url_messages)
        self.assertEqual(res_messages.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_document_isolation(self):
        """Critical Security (Ch. 17.4): Document A's chat session cannot leak into Document B's session."""
        doc_a2 = Document.objects.create(
            user=self.user_a,
            original_filename='usera_contract2.pdf',
            file_reference='uploads/documents/usera_contract2.pdf',
            status=DocumentStatus.COMPLETE
        )

        session_doc1 = ChatSession.objects.create(user=self.user_a, document=self.doc_a)
        ChatMessage.objects.create(session=session_doc1, role=MessageRole.USER, content="Doc 1 query")

        session_doc2 = ChatSession.objects.create(user=self.user_a, document=doc_a2)
        ChatMessage.objects.create(session=session_doc2, role=MessageRole.USER, content="Doc 2 query")

        self.client.force_authenticate(user=self.user_a)
        
        # Querying doc_a messages returns only doc_a messages
        res1 = self.client.get(reverse('document_chat_messages', kwargs={'pk': self.doc_a.id}))
        self.assertEqual(res1.data['count'], 1)
        self.assertEqual(res1.data['results'][0]['content'], "Doc 1 query")

        # Querying doc_a2 messages returns only doc_a2 messages
        res2 = self.client.get(reverse('document_chat_messages', kwargs={'pk': doc_a2.id}))
        self.assertEqual(res2.data['count'], 1)
        self.assertEqual(res2.data['results'][0]['content'], "Doc 2 query")
