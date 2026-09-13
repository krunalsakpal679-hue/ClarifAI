"""
Phase 17 End-to-End User Journey Integration Test (PRD Part B.5, Ch. 30, Ch. 36):
Full journey test against Mock AI Client adapter:
1. Signup new user account
2. Login to obtain access token & httpOnly refresh cookie
3. Upload PDF document
4. Process document to COMPLETE status via background pipeline
5. View Document Summary
6. View Document Clauses list
7. View single Clause detail
8. Execute RAG Chat Session & Message query
9. Upload second PDF document & execute Comparison
10. Generate Document PDF Report & download Report PDF file
11. View Dashboard Summary metrics
12. Delete Document with full cascade & vector cleanup
13. Logout user session
"""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


from apps.documents.models import Document, DocumentStatus
from tasks.comparison_tasks import process_comparison
from tasks.document_tasks import process_document
from tests.test_documents import create_sample_pdf

User = get_user_model()


class EndToEndUserJourneyTestCase(APITestCase):

    def setUp(self):
        cache.clear()
        self.user_email = 'e2e_user@example.com'
        self.user_password = 'Password123!'

    def test_full_user_journey_e2e(self):
        """Executes full end-to-end user lifecycle from signup to logout."""
        
        # 1. SIGNUP
        signup_url = reverse('auth_signup')
        signup_res = self.client.post(signup_url, {
            "email": self.user_email,
            "password": self.user_password
        })
        self.assertEqual(signup_res.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", signup_res.data)
        self.assertIn("user", signup_res.data)

        # 2. LOGIN
        login_url = reverse('auth_login')
        login_res = self.client.post(login_url, {
            "email": self.user_email,
            "password": self.user_password
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        access_token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 3. UPLOAD FIRST DOCUMENT
        doc_upload_url = reverse('document_list_create')
        pdf1_bytes = create_sample_pdf(pages=2)
        pdf1_file = SimpleUploadedFile("master_agreement.pdf", pdf1_bytes, content_type="application/pdf")
        
        upload_res1 = self.client.post(doc_upload_url, {'file': pdf1_file}, format='multipart')
        self.assertEqual(upload_res1.status_code, status.HTTP_201_CREATED)
        doc1_id = upload_res1.data['id']
        self.assertEqual(upload_res1.data['status'], 'queued')

        # 4. PROCESS DOCUMENT (Background Pipeline Execution)
        process_res1 = process_document(doc1_id)
        self.assertIn(process_res1['status'], ['complete', 'already_complete'])

        doc1 = Document.objects.get(id=doc1_id)
        self.assertEqual(doc1.status, DocumentStatus.COMPLETE)


        # 5. VIEW DOCUMENT SUMMARY
        summary_url = reverse('document_summary', kwargs={'pk': doc1_id})
        summary_res = self.client.get(summary_url)
        self.assertEqual(summary_res.status_code, status.HTTP_200_OK)
        self.assertIn('purpose_text', summary_res.data)

        # 6. VIEW CLAUSES LIST
        clauses_url = reverse('document_clause_list', kwargs={'pk': doc1_id})
        clauses_res = self.client.get(clauses_url)
        self.assertEqual(clauses_res.status_code, status.HTTP_200_OK)
        self.assertIn('results', clauses_res.data)
        self.assertGreater(len(clauses_res.data['results']), 0)
        clause1_id = clauses_res.data['results'][0]['id']

        # 7. VIEW SINGLE CLAUSE DETAIL
        clause_detail_url = reverse('document_clause_detail', kwargs={'pk': doc1_id, 'clause_id': clause1_id})
        clause_detail_res = self.client.get(clause_detail_url)
        self.assertEqual(clause_detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(clause_detail_res.data['id'], clause1_id)

        # 8. RAG CHAT QUERY
        chat_messages_url = reverse('document_chat_messages', kwargs={'pk': doc1_id})
        chat_res = self.client.post(chat_messages_url, {'query': 'What is the governing law of this contract?'})
        self.assertEqual(chat_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(chat_res.data['role'], 'assistant')
        self.assertIn('content', chat_res.data)


        # 9. UPLOAD SECOND DOCUMENT & EXECUTE COMPARISON
        pdf2_bytes = create_sample_pdf(pages=2)
        pdf2_file = SimpleUploadedFile("amendment_v2.pdf", pdf2_bytes, content_type="application/pdf")
        upload_res2 = self.client.post(doc_upload_url, {'file': pdf2_file}, format='multipart')
        self.assertEqual(upload_res2.status_code, status.HTTP_201_CREATED)
        doc2_id = upload_res2.data['id']

        process_document(doc2_id)

        comp_create_url = reverse('comparison_list_create')
        comp_res = self.client.post(comp_create_url, {
            'base_document_id': doc1_id,
            'target_document_id': doc2_id
        })
        self.assertIn(comp_res.status_code, [status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED])
        comparison_id = comp_res.data['id']


        # Execute Comparison Task synchronously
        process_comparison(comparison_id)

        comp_detail_url = reverse('comparison_detail', kwargs={'pk': comparison_id})
        comp_detail_res = self.client.get(comp_detail_url)
        self.assertEqual(comp_detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(comp_detail_res.data['status'], 'complete')

        # 10. GENERATE & DOWNLOAD REPORT
        doc_report_url = reverse('document_report_create', kwargs={'pk': doc1_id})
        report_gen_res = self.client.post(doc_report_url)
        self.assertEqual(report_gen_res.status_code, status.HTTP_201_CREATED)
        report_id = report_gen_res.data['id']

        report_download_url = reverse('report_download', kwargs={'pk': report_id})
        report_dl_res = self.client.get(report_download_url)
        self.assertEqual(report_dl_res.status_code, status.HTTP_200_OK)
        self.assertEqual(report_dl_res['Content-Type'], 'application/pdf')

        # 11. VIEW DASHBOARD SUMMARY
        dashboard_url = reverse('dashboard_summary')
        dashboard_res = self.client.get(dashboard_url)
        self.assertEqual(dashboard_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(dashboard_res.data['total_documents'], 2)

        # 12. DELETE DOCUMENT WITH CASCADE
        doc_delete_url = reverse('document_detail_delete', kwargs={'pk': doc1_id})
        with patch("services.ai_client.delete_document_embeddings"):
            delete_res = self.client.delete(doc_delete_url)
        self.assertEqual(delete_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=doc1_id).exists())

        # 13. LOGOUT
        logout_url = reverse('auth_logout')
        logout_res = self.client.post(logout_url)
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)
