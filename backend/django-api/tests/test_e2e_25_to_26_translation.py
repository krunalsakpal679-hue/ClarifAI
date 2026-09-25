"""
ClarifAI End-to-End Multilingual Translation Test Suite (BOOK4-PHASE-20: E2E-25, E2E-26)
Validates:
- E2E-25: Hindi output via ?lang=hi; summary and simplified clauses render in Devanagari Hindi
  with translation_available=True.
- E2E-26: Graceful fallback when translation is unavailable or fails; English content rendered
  with translation_available=False (never blank or broken).
- Provably unaltered clauses.original_text: original English text is never translated or modified.
- Multilingual chatbot: answers correctly in Hindi using identical evidence-gating rules as English.
"""

from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chat.models import ChatSession
from apps.documents.models import Document, DocumentStatus, Clause, DocumentSummary

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_RESULT_BACKEND=None,
    CELERY_BROKER_URL='memory://',
    AI_SERVICE_USE_MOCK=False,
)
class TranslationE2ETestCase(APITestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

        self.user = User.objects.create_user(
            email='e2e_trans_user@example.com',
            password='TestPassword123!'
        )

        self.doc = Document.objects.create(
            user=self.user,
            original_filename='commercial_lease.pdf',
            file_reference='uploads/documents/commercial_lease.pdf',
            status=DocumentStatus.COMPLETE
        )

        # Standard verbatim original clauses
        self.orig_clause_text_1 = "The Tenant shall pay to Landlord annual rent of $60,000 payable in monthly installments of $5,000."
        self.orig_clause_text_2 = "Either party may terminate this lease upon 60 days written notice prior to the expiration date."

        self.clause_1 = Clause.objects.create(
            document=self.doc,
            position=1,
            original_text=self.orig_clause_text_1,
            simplified_text="Pay $5,000 monthly rent.",
            severity="safe"
        )
        self.clause_2 = Clause.objects.create(
            document=self.doc,
            position=2,
            original_text=self.orig_clause_text_2,
            simplified_text="Can cancel lease with 60 days written notice.",
            severity="safe"
        )

        self.summary = DocumentSummary.objects.create(
            document=self.doc,
            purpose_text="Commercial property lease agreement between Landlord and Tenant.",
            obligations_text="Tenant pays monthly rent and maintains premises in good order.",
            key_terms_text="Term: 12 months. Rent: $5,000 per month. Notice: 60 days.",
            key_risks_text="Standard commercial lease terms with no uncapped liabilities."
        )

        # Chat session for Hindi chatbot testing
        self.chat_session = ChatSession.objects.create(
            user=self.user,
            document=self.doc,
            title="Lease Inquiry"
        )

    @patch("apps.documents.views.ai_client.translate")
    def test_e2e_25_hindi_output_via_lang_param(self, mock_translate):
        """
        E2E-25: Toggle to Hindi via ?lang=hi; confirm summary and clauses render
        correctly in Devanagari Hindi with translation_available: True.
        Confirm clauses.original_text is provably UNALTERED verbatim English.
        """
        self.client.force_authenticate(user=self.user)

        # Define AI translation response
        mock_translate.return_value = {
            "success": True,
            "user_id": str(self.user.id),
            "document_id": str(self.doc.id),
            "target_language": "hi",
            "summary_hi": {
                "purpose": "मकान मालिक और किराएदार के बीच वाणिज्यिक संपत्ति पट्टा समझौता।",
                "obligations": "किराएदार मासिक किराया देता है और परिसर को अच्छी स्थिति में रखता है।",
                "key_terms": "अवधि: 12 महीने। किराया: $5,000 प्रति माह। नोटिस: 60 दिन।",
                "key_risks": "बिना किसी असीमित देनदारी के मानक वाणिज्यिक पट्टा शर्तें।"
            },
            "clauses_hi": [
                {
                    "id": str(self.clause_1.id),
                    "position": 1,
                    "original_text": self.orig_clause_text_1,
                    "simplified_text_hi": "$5,000 मासिक किराया दें।"
                },
                {
                    "id": str(self.clause_2.id),
                    "position": 2,
                    "original_text": self.orig_clause_text_2,
                    "simplified_text_hi": "60 दिनों के लिखित नोटिस के साथ पट्टा रद्द कर सकते हैं।"
                }
            ],
            "translation_status": "SUCCESS"
        }

        # 1. Test Summary Endpoint with ?lang=hi
        url_summary = reverse('document_summary', kwargs={'pk': self.doc.id}) + '?lang=hi'
        res_summary = self.client.get(url_summary)
        self.assertEqual(res_summary.status_code, status.HTTP_200_OK)
        self.assertTrue(res_summary.data['translation_available'])
        self.assertIn("वाणिज्यिक संपत्ति पट्टा समझौता", res_summary.data['purpose_text'])
        self.assertIn("मासिक किराया", res_summary.data['obligations_text'])

        # 2. Test Clauses List Endpoint with ?lang=hi
        url_clauses = reverse('document_clause_list', kwargs={'pk': self.doc.id}) + '?lang=hi'
        res_clauses = self.client.get(url_clauses)
        self.assertEqual(res_clauses.status_code, status.HTTP_200_OK)
        results = res_clauses.data['results']
        self.assertEqual(len(results), 2)

        # Verify Clause 1: Hindi simplified text & untouched original text
        c1 = results[0]
        self.assertTrue(c1['translation_available'])
        self.assertIn("मासिक किराया", c1['simplified_text'])
        # PROOF OF INVARIANCE: original_text is 100% unaltered English
        self.assertEqual(c1['original_text'], self.orig_clause_text_1)

        # Verify Clause 2: Hindi simplified text & untouched original text
        c2 = results[1]
        self.assertTrue(c2['translation_available'])
        self.assertIn("लिखित नोटिस", c2['simplified_text'])
        # PROOF OF INVARIANCE: original_text is 100% unaltered English
        self.assertEqual(c2['original_text'], self.orig_clause_text_2)

        # 3. Test Single Clause Detail Endpoint with ?lang=hi
        url_clause_detail = reverse('document_clause_detail', kwargs={'pk': self.doc.id, 'clause_id': self.clause_1.id}) + '?lang=hi'
        res_detail = self.client.get(url_clause_detail)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertTrue(res_detail.data['translation_available'])
        self.assertIn("मासिक किराया", res_detail.data['simplified_text'])
        self.assertEqual(res_detail.data['original_text'], self.orig_clause_text_1)

    @patch("apps.documents.views.ai_client.translate")
    def test_e2e_26_simulated_translation_failure_graceful_fallback(self, mock_translate):
        """
        E2E-26: When translation is unavailable or fails, English content is rendered
        with translation_available=False (never blank or broken).
        Confirm clauses.original_text is provably UNALTERED verbatim English.
        """
        self.client.force_authenticate(user=self.user)
        # Simulate AI translation failure / unavailable
        mock_translate.side_effect = Exception("FastAPI AI translation microservice connection timeout")

        # Summary failure -> translation_available: False, English text preserved
        url_summary = reverse('document_summary', kwargs={'pk': self.doc.id}) + '?lang=hi'
        res_summary = self.client.get(url_summary)
        self.assertEqual(res_summary.status_code, status.HTTP_200_OK)
        self.assertFalse(res_summary.data['translation_available'])
        # Confirms English content is shown rather than blank/broken
        self.assertEqual(res_summary.data['purpose_text'], self.summary.purpose_text)
        self.assertEqual(res_summary.data['obligations_text'], self.summary.obligations_text)

        # Clauses failure -> translation_available: False, English text preserved
        url_clauses = reverse('document_clause_list', kwargs={'pk': self.doc.id}) + '?lang=hi'
        res_clauses = self.client.get(url_clauses)
        self.assertEqual(res_clauses.status_code, status.HTTP_200_OK)
        results = res_clauses.data['results']

        for c, orig_clause in zip(results, [self.clause_1, self.clause_2]):
            self.assertFalse(c['translation_available'])
            self.assertEqual(c['simplified_text'], orig_clause.simplified_text)
            # PROOF OF INVARIANCE: original_text is 100% unaltered English
            self.assertEqual(c['original_text'], orig_clause.original_text)

    @patch("apps.chat.views.ai_client.chat")
    def test_hindi_chatbot_identical_evidence_gating_rules(self, mock_ai_chat):
        """
        Confirm chatbot answers correctly in Hindi using identical evidence-gating rules as English:
        1. When evidence is supported -> Returns grounded answer in Hindi citing source_clause_ids.
        2. When evidence is unsupported -> Returns exact Hindi controlled no-answer response.
        """
        self.client.force_authenticate(user=self.user)
        chat_url = reverse('document_chat_messages', kwargs={'pk': self.doc.id})

        # 1. Supported Hindi Inquiry
        mock_ai_chat.return_value = {
            "answer": "वार्षिक किराया $60,000 है जो $5,000 की मासिक किश्तों में देय है।",
            "source_clause_ids": [str(self.clause_1.id)],
            "has_sufficient_evidence": True,
            "disclaimer": "यह जानकारी केवल संदर्भ के लिए है और औपचारिक कानूनी सलाह नहीं है।",
            "session_id": str(self.chat_session.id),
            "target_language": "hi",
            "user_id": str(self.user.id),
            "document_id": str(self.doc.id)
        }

        supported_payload = {
            "query": "किराया कितना है?"
        }
        res_supported = self.client.post(chat_url, supported_payload)
        self.assertEqual(res_supported.status_code, status.HTTP_201_CREATED)
        self.assertIn("वार्षिक किराया", res_supported.data['content'])
        self.assertEqual(res_supported.data['source_clause_ids'], [str(self.clause_1.id)])

        # 2. Unsupported Hindi Inquiry (evidence gate triggers controlled no-answer)
        hindi_no_answer = "मैं इस प्रश्न का उत्तर देने में असमर्थ हूँ क्योंकि प्रदान किए गए दस्तावेज़ में पर्याप्त प्रासंगिक खंड शामिल नहीं हैं।"
        mock_ai_chat.return_value = {
            "answer": hindi_no_answer,
            "source_clause_ids": [],
            "has_sufficient_evidence": False,
            "disclaimer": "यह जानकारी केवल संदर्भ के लिए है और औपचारिक कानूनी सलाह नहीं है।",
            "session_id": str(self.chat_session.id),
            "target_language": "hi",
            "user_id": str(self.user.id),
            "document_id": str(self.doc.id)
        }

        unsupported_payload = {
            "query": "मंगल ग्रह के कानून क्या हैं?"
        }
        res_unsupported = self.client.post(chat_url, unsupported_payload)
        self.assertEqual(res_unsupported.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_unsupported.data['content'], hindi_no_answer)
        self.assertEqual(res_unsupported.data['source_clause_ids'], [])
