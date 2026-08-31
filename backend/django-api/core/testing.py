"""
Reusable test utilities and fixtures for IDOR security testing (PRD Ch. 34.4 & Phase 16).
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class IDORTestMixin:
    """
    Reusable test mixin providing two distinct users and assertions for IDOR security testing.
    All resource test suites (Phases 4-16) use this mixin to verify non-owners receive 404, never 403.
    """
    def create_two_users(self):
        """
        Creates user_a (primary owner) and user_b (potential unauthorized accessor).
        """
        self.user_a = User.objects.create_user(
            email='user_a_owner@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            email='user_b_unauthorized@example.com',
            password='Password123!'
        )

        refresh_a = RefreshToken.for_user(self.user_a)
        refresh_b = RefreshToken.for_user(self.user_b)

        self.token_a = str(refresh_a.access_token)
        self.token_b = str(refresh_b.access_token)

        self.auth_headers_a = {'HTTP_AUTHORIZATION': f'Bearer {self.token_a}'}
        self.auth_headers_b = {'HTTP_AUTHORIZATION': f'Bearer {self.token_b}'}

    def assert_idor_protection(self, client, resource_url, method='get', data=None):
        """
        Asserts that user_b accessing user_a's resource returns HTTP 404 NOT FOUND, NEVER HTTP 403.
        """
        http_method = getattr(client, method.lower())
        kwargs = dict(self.auth_headers_b)
        if data is not None and method.lower() in ('post', 'put', 'patch'):
            kwargs['data'] = data
            kwargs['content_type'] = 'application/json'

        response = http_method(resource_url, **kwargs)

        # Assert HTTP 404 Not Found (NEVER 403 Forbidden)
        self.assertNotEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Security Violation: Ownership failure returned 403 Forbidden instead of masking with 404 Not Found!"
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            f"Expected HTTP 404 Not Found on cross-user access, got HTTP {response.status_code}"
        )

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'NOT_FOUND')
        return response
