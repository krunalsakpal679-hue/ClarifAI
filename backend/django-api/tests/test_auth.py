"""
Phase 2 Authentication & Security Unit Tests:
- AC-1.1: Valid signup creates & authenticates user
- AC-1.2: Duplicate signup rejected
- AC-1.3: Logout revokes refresh token & blocks protected pages
- Endpoints matching Ch. 30.1
- Refresh token in httpOnly cookie
- Generic invalid login error (Ch. 32)
- Rate limiting on signup/login
"""
import time
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthenticationTestCase(TestCase):

    def setUp(self):
        cache.clear()
        self.signup_url = '/api/auth/signup'
        self.login_url = '/api/auth/login'
        self.refresh_url = '/api/auth/refresh'
        self.logout_url = '/api/auth/logout'

        self.user_email = 'user1@example.com'
        self.user_password = 'Password123!'

    def tearDown(self):
        cache.clear()

    def test_ac1_1_valid_signup_creates_and_authenticates_user(self):
        """AC-1.1: Valid signup creates user with hashed password, returns access token, sets httpOnly cookie."""
        payload = {
            "email": self.user_email,
            "password": self.user_password,
        }
        response = self.client.post(self.signup_url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], self.user_email)
        self.assertIn('id', data['user'])
        self.assertIn('access', data)

        # Confirm user exists in DB with hashed password (never plain text)
        user = User.objects.get(email=self.user_email)
        self.assertTrue(user.check_password(self.user_password))
        self.assertNotEqual(user.password, self.user_password)

        # Confirm refresh token is set in httpOnly cookie and NOT in JSON body
        self.assertNotIn('refresh', data)
        self.assertIn('refresh_token', response.cookies)
        cookie = response.cookies['refresh_token']
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Lax')

    def test_ac1_2_duplicate_signup_rejected(self):
        """AC-1.2: Duplicate signup is rejected with Ch. 30.8 VALIDATION_ERROR and no duplicate account created."""
        User.objects.create_user(email=self.user_email, password=self.user_password)
        initial_count = User.objects.count()

        payload = {
            "email": self.user_email,
            "password": "AnotherPassword123!",
        }
        response = self.client.post(self.signup_url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('details', data['error'])

        # Confirm no duplicate user created
        self.assertEqual(User.objects.count(), initial_count)

    def test_login_valid_credentials(self):
        """Valid login returns access token and httpOnly refresh cookie."""
        User.objects.create_user(email=self.user_email, password=self.user_password)

        payload = {
            "email": self.user_email,
            "password": self.user_password,
        }
        response = self.client.post(self.login_url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('access', data)
        self.assertNotIn('refresh', data)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token']['httponly'])

    def test_login_invalid_credentials_generic_error(self):
        """Invalid login credentials return generic AUTHENTICATION_FAILED without field leakage (Ch. 32)."""
        User.objects.create_user(email=self.user_email, password=self.user_password)

        payload = {
            "email": self.user_email,
            "password": "WrongPassword123!",
        }
        response = self.client.post(self.login_url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error']['message'], 'Invalid email or password.')

    def test_token_refresh_rotation_and_blacklisting(self):
        """Refresh token request rotates tokens and invalidates the old refresh token."""
        user = User.objects.create_user(email=self.user_email, password=self.user_password)
        refresh = RefreshToken.for_user(user)

        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh_token', response.cookies)

        new_refresh = response.cookies['refresh_token'].value
        self.assertNotEqual(str(refresh), new_refresh)

        # Attempt to reuse old refresh token -> should be rejected as blacklisted/invalid
        self.client.cookies['refresh_token'] = str(refresh)
        reused_response = self.client.post(self.refresh_url)
        self.assertEqual(reused_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ac1_3_logout_blacklists_token_and_clears_cookie(self):
        """AC-1.3: Logout revokes refresh token server-side and clears cookie; protected pages require re-auth."""
        user = User.objects.create_user(email=self.user_email, password=self.user_password)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Execute logout with Authorization header and httpOnly cookie
        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post(
            self.logout_url,
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Confirm cookie was deleted/cleared
        self.assertEqual(response.cookies['refresh_token'].value, '')

        # Confirm refresh token was blacklisted in DB
        self.client.cookies['refresh_token'] = str(refresh)
        refresh_attempt = self.client.post(self.refresh_url)
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rate_limiting_on_login(self):
        """Rate limiting triggers on auth endpoints after configured threshold (5/minute)."""
        payload = {"email": "nonexistent@example.com", "password": "password"}

        for _ in range(5):
            self.client.post(self.login_url, data=payload, content_type='application/json')

        # 6th attempt within minute should trigger HTTP 429 RATE_LIMITED
        exceeded_response = self.client.post(self.login_url, data=payload, content_type='application/json')
        self.assertEqual(exceeded_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        data = exceeded_response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'RATE_LIMITED')
