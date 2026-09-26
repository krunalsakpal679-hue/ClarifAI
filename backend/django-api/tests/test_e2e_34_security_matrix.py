"""
BOOK4-PHASE-24: Full System Security Audit & Two-User Authorization Matrix (E2E-34)
Source Traceability: PRD v2.3 Chapter 26 (Security & Privacy), Chapter 27 (Threat Model), Chapter 30 (API Specification)

Test Matrix Coverage:
1. Enumerate every owner-scoped endpoint from docs/integration-contract-matrix.md; attempt access
   with a second user's token for each; confirm 404-equivalent, never 403 or data leakage.
2. Test JWT tampering (modified payload, expired token, malformed token); confirm rejection (401).
3. Test refresh-cookie theft scenarios are mitigated by httpOnly/secure/samesite flags and omission from JSON.
4. Test CORS configuration rejects an unapproved origin (omits Access-Control-Allow-Origin).
5. Test upload security:
   - Path traversal in filenames (neutralized via basename sanitization)
   - SQL injection in text fields (handled via Django ORM parameterization)
   - XSS in user-supplied text (treated as raw text, no execution/unescaped rendering)
   - SSRF via URL fields (zero public URL-fetching attack surface)
6. Test rate limiting on login, upload, and chatbot endpoints under real repeated requests (HTTP 429).
7. Test that no error response ever leaks a stack trace, internal file path, or secret value.
8. Confirm the INTERNAL_SERVICE_SECRET between Django and FastAPI is genuinely enforced under unauthorized requests.
"""

import io
import json
import time
from datetime import timedelta
from unittest.mock import MagicMock, patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.chat.models import ChatMessage, ChatSession, MessageRole
from apps.comparison.models import Comparison, ComparisonStatus
from apps.documents.models import Clause, ClauseSeverity, Document, DocumentStatus, DocumentSummary
from apps.reports.models import Report, ReportStatus

User = get_user_model()

# Valid minimal PDF header and trailer
MINIMAL_VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
)


class E2E34TwoUserAuthorizationAndSecurityMatrixTestCase(APITestCase):
    """
    Complete security test matrix verifying two-user authorization and adversarial robustness.
    """

    def setUp(self):
        cache.clear()

        # User A (Resource Owner)
        self.user_a = User.objects.create_user(
            email="usera_security@clarifai.io",
            password="SecurePassword123!"
        )
        self.token_a = str(RefreshToken.for_user(self.user_a).access_token)

        # User B (Adversary / Second User)
        self.user_b = User.objects.create_user(
            email="userb_attacker@clarifai.io",
            password="AttackerPassword123!"
        )
        self.token_b = str(RefreshToken.for_user(self.user_b).access_token)

        # User A's Document
        self.doc_a = Document.objects.create(
            user=self.user_a,
            original_filename="usera_confidential_contract.pdf",
            file_reference="uploads/documents/usera_confidential_contract.pdf",
            status=DocumentStatus.COMPLETE
        )
        self.summary_a = DocumentSummary.objects.create(
            document=self.doc_a,
            purpose_text="User A Confidential purpose.",
            key_risks_text="User A Secret risks."
        )
        self.clause_a = Clause.objects.create(
            document=self.doc_a,
            position=1,
            original_text="Confidential liability clause of User A.",
            simplified_text="Simplified liability clause of User A.",
            category="LIABILITY",
            severity=ClauseSeverity.HIGH
        )

        # User A's Chat Session & Message
        self.chat_session_a = ChatSession.objects.create(
            user=self.user_a,
            document=self.doc_a,
            title="User A Private Chat"
        )
        self.chat_message_a = ChatMessage.objects.create(
            session=self.chat_session_a,
            role=MessageRole.USER,
            content="What are the secret liabilities?",
            source_clause_ids=[str(self.clause_a.id)]
        )

        # User A's Target Document & Comparison
        self.doc_a_target = Document.objects.create(
            user=self.user_a,
            original_filename="usera_comparison_target.pdf",
            file_reference="uploads/documents/usera_comparison_target.pdf",
            status=DocumentStatus.COMPLETE
        )
        self.comparison_a = Comparison.objects.create(
            user=self.user_a,
            base_document=self.doc_a,
            target_document=self.doc_a_target,
            status=ComparisonStatus.COMPLETE
        )

        # User A's Report
        self.report_a = Report.objects.create(
            user=self.user_a,
            document=self.doc_a,
            status=ReportStatus.COMPLETE,
            file_reference="uploads/reports/usera_secret_report.pdf"
        )

        # User B's own Document (for cross-user comparison attempts)
        self.doc_b = Document.objects.create(
            user=self.user_b,
            original_filename="userb_legitimate_doc.pdf",
            file_reference="uploads/documents/userb_legitimate_doc.pdf",
            status=DocumentStatus.COMPLETE
        )

    def tearDown(self):
        cache.clear()

    # =========================================================================
    # ITEM 1: Owner-Scoped Endpoint IDOR Matrix (User B Accessing User A Resources)
    # PRD Ch. 26.5: MUST return HTTP 404 Not Found (Never 403, Never data leakage)
    # =========================================================================

    def test_idor_01_document_detail_returns_404(self):
        """User B requesting User A's document detail receives 404 Not Found."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_detail_delete", kwargs={"pk": self.doc_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_idor_02_document_delete_returns_404(self):
        """User B attempting to delete User A's document receives 404 and doc remains."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_detail_delete", kwargs={"pk": self.doc_a.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Document.objects.filter(id=self.doc_a.id).exists())

    def test_idor_03_document_summary_returns_404(self):
        """User B requesting User A's document summary receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_summary", kwargs={"pk": self.doc_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn("User A Confidential purpose", response.content.decode())

    def test_idor_04_document_clause_list_returns_404(self):
        """User B requesting User A's document clause list receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_clause_list", kwargs={"pk": self.doc_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn("Confidential liability clause", response.content.decode())

    def test_idor_05_document_clause_detail_returns_404(self):
        """User B requesting User A's clause detail receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_clause_detail", kwargs={"pk": self.doc_a.id, "clause_id": self.clause_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_06_chat_sessions_get_returns_404(self):
        """User B querying chat session for User A's document receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_chat_sessions", kwargs={"pk": self.doc_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_07_chat_messages_get_returns_404(self):
        """User B querying chat messages for User A's document receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_chat_messages", kwargs={"pk": self.doc_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn("What are the secret liabilities?", response.content.decode())

    def test_idor_08_chat_messages_post_returns_404(self):
        """User B sending a chat message to User A's document receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_chat_messages", kwargs={"pk": self.doc_a.id})
        response = self.client.post(url, {"query": "Tell me secrets."}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_09_comparison_create_with_usera_base_returns_404(self):
        """User B attempting comparison using User A's base document receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("comparison_list_create")
        response = self.client.post(
            url,
            {"base_document_id": str(self.doc_a.id), "target_document_id": str(self.doc_b.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_10_comparison_create_with_usera_target_returns_404(self):
        """User B attempting comparison using User A's target document receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("comparison_list_create")
        response = self.client.post(
            url,
            {"base_document_id": str(self.doc_b.id), "target_document_id": str(self.doc_a.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_11_comparison_detail_returns_404(self):
        """User B requesting User A's comparison detail receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("comparison_detail", kwargs={"pk": self.comparison_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_12_document_report_create_returns_404(self):
        """User B attempting to trigger report creation for User A's document receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_report_create", kwargs={"pk": self.doc_a.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_13_comparison_report_create_returns_404(self):
        """User B attempting to trigger report creation for User A's comparison receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("comparison_report_create", kwargs={"pk": self.comparison_a.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_14_report_download_returns_404(self):
        """User B attempting to download User A's completed report receives 404."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("report_download", kwargs={"pk": self.report_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_idor_15_document_list_never_leaks_other_users_records(self):
        """User B document list returns strictly User B's documents, zero records of User A."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("document_list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get("results", [])
        doc_ids = [d["id"] for d in results]
        self.assertIn(str(self.doc_b.id), doc_ids)
        self.assertNotIn(str(self.doc_a.id), doc_ids)
        self.assertNotIn(str(self.doc_a_target.id), doc_ids)

    def test_idor_16_dashboard_summary_strictly_scoped_to_user(self):
        """User B dashboard metrics compute solely User B's documents."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")
        url = reverse("dashboard_summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # User B has exactly 1 document
        self.assertEqual(data["total_documents"], 1)

    # =========================================================================
    # ITEM 2: JWT Tampering & Adversarial Token Tests
    # =========================================================================

    def test_jwt_tampered_payload_rejected(self):
        """A token with a tampered payload/signature is strictly rejected with 401."""
        # Create valid token then mutate characters in payload
        parts = self.token_a.split(".")
        tampered_token = f"{parts[0]}.eyJob2dnd2FydHMiOiJ0cnVlIn0.{parts[2]}"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered_token}")
        response = self.client.get(reverse("document_list_create"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_FAILED")

    def test_jwt_expired_token_rejected(self):
        """An expired token is strictly rejected with 401."""
        token = AccessToken.for_user(self.user_a)
        # Manually force expiration into the past
        token.set_exp(lifetime=-timedelta(minutes=10))
        expired_token_str = str(token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired_token_str}")
        response = self.client.get(reverse("document_list_create"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_FAILED")

    def test_jwt_malformed_token_rejected(self):
        """Malformed garbage tokens are strictly rejected with 401."""
        malformed_tokens = [
            "NotAJwtTokenAtAll",
            "Bearer ",
            "part1.part2",
            "Bearer invalid.token.structure.extra",
            "Bearer null",
        ]
        for bad_token in malformed_tokens:
            self.client.credentials(HTTP_AUTHORIZATION=bad_token)
            response = self.client.get(reverse("document_list_create"))
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Failed to reject malformed token: {bad_token}"
            )
            self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_FAILED")

    # =========================================================================
    # ITEM 3: Refresh Cookie Theft Mitigation (httpOnly, SameSite, Secure)
    # =========================================================================

    def test_refresh_cookie_security_flags_on_login(self):
        """Login sets refresh cookie with httpOnly=True, SameSite=Lax, and never in JSON body."""
        client = APIClient()
        response = client.post(
            reverse("auth_login"),
            {"email": "usera_security@clarifai.io", "password": "SecurePassword123!"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure refresh token is NOT in JSON body
        self.assertNotIn("refresh", response.json())
        self.assertNotIn("refresh_token", response.json())

        # Ensure refresh cookie has secure flags
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertTrue(cookie["httponly"], "Cookie must be httpOnly to prevent XSS theft")
        self.assertEqual(cookie["samesite"], "Lax", "Cookie SameSite must be Lax to prevent CSRF")

    def test_refresh_cookie_security_flags_on_signup(self):
        """Signup sets refresh cookie with httpOnly=True, SameSite=Lax, and never in JSON body."""
        client = APIClient()
        response = client.post(
            reverse("auth_signup"),
            {
                "email": "new_secure_user@clarifai.io",
                "password": "SecurePassword123!",
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("refresh", response.json())
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    # =========================================================================
    # ITEM 4: CORS Configuration (Rejects Unapproved Origins)
    # =========================================================================

    def test_cors_rejects_unapproved_origin(self):
        """Requests with unapproved Origin do not receive Access-Control-Allow-Origin header."""
        client = APIClient()
        response = client.get(
            "/api/auth/login",
            HTTP_ORIGIN="http://evil-attacker-site.com"
        )
        # django-cors-headers does not set Access-Control-Allow-Origin for unapproved origins
        allow_origin = response.headers.get("Access-Control-Allow-Origin")
        self.assertNotEqual(allow_origin, "http://evil-attacker-site.com")
        self.assertNotEqual(allow_origin, "*")

    def test_cors_accepts_approved_origin(self):
        """Requests with approved Origin receive matching Access-Control-Allow-Origin header."""
        client = APIClient()
        response = client.get(
            "/api/auth/login",
            HTTP_ORIGIN="http://localhost:5173"
        )
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")

    # =========================================================================
    # ITEM 5: Upload Security & Injection Defense
    # =========================================================================

    def test_upload_security_path_traversal_filename_sanitized(self):
        """Path traversal characters in uploaded filename (../../etc/passwd) are neutralized."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        adversarial_filename = "../../../../etc/passwd.pdf"
        pdf_file = SimpleUploadedFile(
            adversarial_filename,
            MINIMAL_VALID_PDF,
            content_type="application/pdf"
        )

        with patch("apps.documents.views.process_document.delay"):
            response = self.client.post(
                reverse("document_list_create"),
                {"file": pdf_file},
                format="multipart"
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc = Document.objects.get(id=response.json()["id"])
        # Original filename sanitized to basename
        self.assertNotIn("..", doc.original_filename)
        self.assertNotIn("/", doc.original_filename)
        self.assertNotIn("\\", doc.original_filename)
        self.assertEqual(doc.original_filename, "passwd.pdf")
        # File reference does not escape uploads/documents
        self.assertTrue(doc.file_reference.startswith("uploads/documents/"))
        self.assertNotIn("..", doc.file_reference)

    def test_sql_injection_defense_in_text_and_query_fields(self):
        """SQL injection payloads in chat content and search parameters are safe via ORM parameterization."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        sql_payloads = [
            "'; DROP TABLE documents; --",
            "' OR '1'='1",
            "1' UNION SELECT username, password FROM users_customuser --",
            "'; WAITFOR DELAY '0:0:5'--",
        ]
        url = reverse("document_chat_messages", kwargs={"pk": self.doc_a.id})
        for payload in sql_payloads:
            with patch("services.ai_client.client.RealAIClient.chat") as mock_chat:
                mock_chat.return_value = {
                    "answer": "Safe response to query.",
                    "source_clause_ids": []
                }
                response = self.client.post(url, {"query": payload}, format="json")
                # Must either succeed safely or fail gracefully; DB must remain intact
                self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
                # Verify documents table still exists and is untouched
                self.assertTrue(Document.objects.filter(id=self.doc_a.id).exists())

    def test_xss_in_user_supplied_text_treated_as_plain_data(self):
        """XSS payloads in user input are treated strictly as plain string data in responses."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        xss_payload = "<script>alert('XSS-Exploit')</script><img src=x onerror=alert(1)>"
        url = reverse("document_chat_messages", kwargs={"pk": self.doc_a.id})
        with patch("services.ai_client.client.RealAIClient.chat") as mock_chat:
            mock_chat.return_value = {
                "answer": "Sanitized response",
                "source_clause_ids": []
            }
            response = self.client.post(url, {"query": xss_payload}, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            # Response content-type must be application/json (never text/html)
            self.assertEqual(response["Content-Type"], "application/json")
            # User message is saved and retrieved safely as data
            user_msg = ChatMessage.objects.filter(session__document=self.doc_a, role=MessageRole.USER).latest("created_at")
            self.assertEqual(user_msg.content, xss_payload)
            # Message list endpoint returns payload safely as plain JSON string
            list_res = self.client.get(url)
            self.assertEqual(list_res.status_code, status.HTTP_200_OK)
            self.assertEqual(list_res["Content-Type"], "application/json")
            self.assertIn(xss_payload, list_res.content.decode())

    def test_ssrf_defense_zero_remote_url_fetching_endpoints(self):
        """ClarifAI exposes zero endpoints that accept or fetch arbitrary remote URLs."""
        # Attempting to post a remote URL to document creation is rejected by FileField
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        response = self.client.post(
            reverse("document_list_create"),
            {"file": "http://169.254.169.254/latest/meta-data/"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    # =========================================================================
    # ITEM 6: Rate Limiting Under Real Repeated Requests (HTTP 429)
    # =========================================================================

    def test_rate_limiting_on_login_repeated_requests(self):
        """5 rapid login attempts succeed; the 6th attempt is throttled with HTTP 429 and Retry-After."""
        cache.clear()
        client = APIClient()
        login_url = reverse("auth_login")
        payload = {"email": "nonexistent@clarifai.io", "password": "WrongPassword!"}

        for i in range(5):
            res = client.post(login_url, payload, format="json")
            self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # 6th attempt should be blocked by rate limit
        throttled_res = client.post(login_url, payload, format="json")
        self.assertEqual(throttled_res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(throttled_res.json()["error"]["code"], "RATE_LIMITED")
        self.assertIn("Retry-After", throttled_res.headers)

    def test_rate_limiting_on_upload_endpoint(self):
        """Upload endpoint enforces rate limiting after configured quota."""
        cache.clear()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        upload_url = reverse("document_list_create")

        with patch.object(ScopedRateThrottle, "get_rate", return_value="3/minute"):
            with patch("apps.documents.views.process_document.delay"):
                for i in range(3):
                    pdf_file = SimpleUploadedFile(f"rate_test_{i}.pdf", MINIMAL_VALID_PDF, content_type="application/pdf")
                    res = self.client.post(upload_url, {"file": pdf_file}, format="multipart")
                    self.assertEqual(res.status_code, status.HTTP_201_CREATED)

                # 4th upload attempt exceeds quota
                pdf_file = SimpleUploadedFile("rate_test_exceeded.pdf", MINIMAL_VALID_PDF, content_type="application/pdf")
                throttled_res = self.client.post(upload_url, {"file": pdf_file}, format="multipart")
                self.assertEqual(throttled_res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertEqual(throttled_res.json()["error"]["code"], "RATE_LIMITED")
                self.assertIn("Retry-After", throttled_res.headers)

    def test_rate_limiting_on_chatbot_endpoint(self):
        """Chatbot endpoint enforces rate limiting after configured quota."""
        cache.clear()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")
        chat_url = reverse("document_chat_messages", kwargs={"pk": self.doc_a.id})

        with patch.object(ScopedRateThrottle, "get_rate", return_value="3/minute"):
            with patch("services.ai_client.client.RealAIClient.chat") as mock_chat:
                mock_chat.return_value = {"answer": "Ok", "source_clause_ids": []}
                for i in range(3):
                    res = self.client.post(chat_url, {"query": f"Question {i}"}, format="json")
                    self.assertEqual(res.status_code, status.HTTP_201_CREATED)

                # 4th question exceeds quota
                throttled_res = self.client.post(chat_url, {"query": "Question exceeded"}, format="json")
                self.assertEqual(throttled_res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
                self.assertEqual(throttled_res.json()["error"]["code"], "RATE_LIMITED")
                self.assertIn("Retry-After", throttled_res.headers)

    # =========================================================================
    # ITEM 7: Information & Secret Leakage Prevention
    # =========================================================================

    def test_error_envelope_never_leaks_stack_traces_paths_or_secrets(self):
        """500 Internal Server Errors return clean structured JSON without file paths or tracebacks."""
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        from core.exceptions import custom_exception_handler

        class CrashingView(APIView):
            def get(self, request):
                # Simulate crash with sensitive info in exception
                raise RuntimeError(
                    f"Fatal DB Error on C:\\clarifai\\secrets.txt with SECRET={settings.SECRET_KEY}"
                )

        factory = APIRequestFactory()
        request = factory.get("/api/crash-test/")
        try:
            view = CrashingView.as_view()
            response = view(request)
        except Exception as exc:
            response = custom_exception_handler(exc, {"request": request, "view": CrashingView()})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        response_json = json.dumps(response.data)

        # Confirm structured Ch. 30.8 envelope
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"]["code"], "INTERNAL_SERVER_ERROR")
        self.assertEqual(response.data["error"]["message"], "An internal server error occurred.")

        # Confirm zero leakage of stack trace, file path, or secrets
        self.assertNotIn("Traceback", response_json)
        self.assertNotIn("secrets.txt", response_json)
        self.assertNotIn("C:\\\\clarifai", response_json)
        self.assertNotIn(settings.SECRET_KEY, response_json)

    # =========================================================================
    # ITEM 8: Internal Service Secret Enforcement (Django <-> FastAPI AI)
    # =========================================================================

    def test_fastapi_internal_secret_rejection_when_unauthorized(self):
        """FastAPI verify_internal_secret raises HTTP 403 when secret is missing or invalid."""
        import asyncio
        import sys
        from pathlib import Path
        fastapi_dir = str(Path(settings.BASE_DIR).parent / "fastapi-ai")
        if fastapi_dir not in sys.path:
            sys.path.insert(0, fastapi_dir)

        try:
            from fastapi import HTTPException
            from app.core.security import verify_internal_secret
            from app.core.config import settings as fastapi_settings
        except ImportError:
            self.skipTest("FastAPI is not installed in the Django environment (tested in AI microservice suite).")

        # Save and configure test secret in fastapi settings
        orig_secret = fastapi_settings.INTERNAL_SERVICE_SECRET
        orig_env = fastapi_settings.ENVIRONMENT
        try:
            fastapi_settings.INTERNAL_SERVICE_SECRET = "production-super-secret-12345"
            fastapi_settings.ENVIRONMENT = "production"

            # Case 1: Missing secret header -> HTTP 403
            with self.assertRaises(HTTPException) as cm_missing:
                asyncio.run(verify_internal_secret(x_internal_service_secret=None))
            self.assertEqual(cm_missing.exception.status_code, 403)
            self.assertIn("Invalid or missing internal service secret", cm_missing.exception.detail)

            # Case 2: Incorrect secret header -> HTTP 403
            with self.assertRaises(HTTPException) as cm_wrong:
                asyncio.run(verify_internal_secret(x_internal_service_secret="wrong-attacker-secret"))
            self.assertEqual(cm_wrong.exception.status_code, 403)
            self.assertIn("Invalid or missing internal service secret", cm_wrong.exception.detail)

            # Case 3: Valid secret header -> Allowed (returns True)
            result = asyncio.run(verify_internal_secret(x_internal_service_secret="production-super-secret-12345"))
            self.assertTrue(result)
        finally:
            fastapi_settings.INTERNAL_SERVICE_SECRET = orig_secret
            fastapi_settings.ENVIRONMENT = orig_env
