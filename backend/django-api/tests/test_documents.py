"""
Phase 5 Document Model & PDF Upload Pipeline Unit & Security Tests:
- Valid PDF upload succeeds (status=queued)
- Oversized file rejected (>20MB)
- Non-PDF / wrong header rejected
- Corrupted / empty PDF rejected at structure validation step
- Password-protected PDF rejected with distinct message (R-12)
- Duplicate upload allowed with no deduplication (R-14)
- List/Detail/Delete endpoints match Ch. 30.2 (IsOwner 404-not-403 IDOR protection)
"""
import io
import os
import pypdf
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status

from apps.documents.models import Document, DocumentStatus
from core.testing import IDORTestMixin


def create_sample_pdf(pages=1, password=None):
    """Utility helper to generate in-memory valid or password-protected PDF bytes."""
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    if password:
        writer.encrypt(password)
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()


class DocumentUploadTestCase(TestCase, IDORTestMixin):

    def setUp(self):
        self.create_two_users()
        self.upload_url = '/api/documents/'

    def test_valid_pdf_upload_succeeds(self):
        """Valid PDF upload creates a Document record with status=queued."""
        pdf_bytes = create_sample_pdf(pages=2)
        uploaded_file = SimpleUploadedFile(
            name='sample_agreement.pdf',
            content=pdf_bytes,
            content_type='application/pdf'
        )

        response = self.client.post(
            self.upload_url,
            data={'file': uploaded_file},
            **self.auth_headers_a
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['original_filename'], 'sample_agreement.pdf')
        self.assertEqual(data['status'], 'queued')
        self.assertIn('id', data)

        # Verify DB record created
        doc = Document.objects.get(id=data['id'])
        self.assertEqual(doc.user, self.user_a)
        self.assertEqual(doc.status, DocumentStatus.QUEUED)

    def test_oversized_file_rejected(self):
        """File larger than MAX_UPLOAD_SIZE_MB (20MB) is rejected."""
        max_bytes = 20 * 1024 * 1024
        # Fake large file larger than 20MB
        large_content = b'%PDF-1.4\n' + (b'x' * (max_bytes + 1024))
        large_file = SimpleUploadedFile(
            name='large_file.pdf',
            content=large_content,
            content_type='application/pdf'
        )

        response = self.client.post(
            self.upload_url,
            data={'file': large_file},
            **self.auth_headers_a
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('20MB', str(data['error']['details']))

    def test_non_pdf_file_rejected(self):
        """File without genuine %PDF- magic bytes header is rejected."""
        fake_file = SimpleUploadedFile(
            name='malicious_script.pdf',
            content=b'<html><body>Not a PDF</body></html>',
            content_type='application/pdf'
        )

        response = self.client.post(
            self.upload_url,
            data={'file': fake_file},
            **self.auth_headers_a
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('genuine PDF', str(data['error']['details']))

    def test_corrupted_empty_pdf_rejected(self):
        """Corrupted or unparseable PDF stream is rejected at structure validation step."""
        corrupted_file = SimpleUploadedFile(
            name='corrupted.pdf',
            content=b'%PDF-1.4 truncated corrupted stream content without valid PDF catalog structure',
            content_type='application/pdf'
        )

        response = self.client.post(
            self.upload_url,
            data={'file': corrupted_file},
            **self.auth_headers_a
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('corrupted', str(data['error']['details']).lower())

    def test_password_protected_pdf_rejected_with_distinct_message(self):
        """Password-protected PDF is rejected with distinct error message (R-12), separate from corrupted rejection."""
        encrypted_pdf_bytes = create_sample_pdf(password='Secret123!')
        encrypted_file = SimpleUploadedFile(
            name='encrypted_agreement.pdf',
            content=encrypted_pdf_bytes,
            content_type='application/pdf'
        )

        response = self.client.post(
            self.upload_url,
            data={'file': encrypted_file},
            **self.auth_headers_a
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        # Explicit assertion: Password-protected message is distinct from corrupted message
        self.assertIn('Password-protected PDFs are not supported', str(data['error']['details']))
        self.assertNotIn('corrupted', str(data['error']['details']).lower())

    def test_duplicate_uploads_allowed(self):
        """Duplicate uploads of identical file succeed without deduplication logic (R-14)."""
        pdf_bytes = create_sample_pdf(pages=1)
        file1 = SimpleUploadedFile('duplicate.pdf', pdf_bytes, content_type='application/pdf')
        file2 = SimpleUploadedFile('duplicate.pdf', pdf_bytes, content_type='application/pdf')

        res1 = self.client.post(self.upload_url, data={'file': file1}, **self.auth_headers_a)
        res2 = self.client.post(self.upload_url, data={'file': file2}, **self.auth_headers_a)

        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        data1 = res1.json()
        data2 = res2.json()
        self.assertNotEqual(data1['id'], data2['id'])
        self.assertEqual(Document.objects.filter(user=self.user_a).count(), 2)

    def test_list_documents_owner_scoped(self):
        """GET /api/documents/ returns only the authenticated user's documents."""
        pdf_bytes = create_sample_pdf()
        f_a = SimpleUploadedFile('doc_a.pdf', pdf_bytes, content_type='application/pdf')
        f_b = SimpleUploadedFile('doc_b.pdf', pdf_bytes, content_type='application/pdf')

        self.client.post(self.upload_url, data={'file': f_a}, **self.auth_headers_a)
        self.client.post(self.upload_url, data={'file': f_b}, **self.auth_headers_b)

        # User A list
        res_a = self.client.get(self.upload_url, **self.auth_headers_a)
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        results_a = res_a.json()['results']
        self.assertEqual(len(results_a), 1)
        self.assertEqual(results_a[0]['original_filename'], 'doc_a.pdf')

        # User B list
        res_b = self.client.get(self.upload_url, **self.auth_headers_b)
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        results_b = res_b.json()['results']
        self.assertEqual(len(results_b), 1)
        self.assertEqual(results_b[0]['original_filename'], 'doc_b.pdf')

    def test_detail_and_delete_documents_ownership_enforcement(self):
        """GET & DELETE /api/documents/{id}/ allow owner access and return 404 for non-owners (IsOwner)."""
        pdf_bytes = create_sample_pdf()
        f_a = SimpleUploadedFile('doc_owner.pdf', pdf_bytes, content_type='application/pdf')
        create_res = self.client.post(self.upload_url, data={'file': f_a}, **self.auth_headers_a)
        doc_id = create_res.json()['id']
        detail_url = f'/api/documents/{doc_id}/'

        # Owner GET -> 200 OK
        res_get_a = self.client.get(detail_url, **self.auth_headers_a)
        self.assertEqual(res_get_a.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get_a.json()['status'], 'queued')

        # Non-owner GET -> 404 NOT FOUND (IsOwner IDOR protection)
        self.assert_idor_protection(client=self.client, resource_url=detail_url, method='get')

        # Non-owner DELETE -> 404 NOT FOUND (IsOwner IDOR protection)
        self.assert_idor_protection(client=self.client, resource_url=detail_url, method='delete')

        # Owner DELETE -> 204 NO CONTENT
        res_del_a = self.client.delete(detail_url, **self.auth_headers_a)
        self.assertEqual(res_del_a.status_code, status.HTTP_204_NO_CONTENT)

        # Confirm Document record deleted
        self.assertFalse(Document.objects.filter(id=doc_id).exists())
