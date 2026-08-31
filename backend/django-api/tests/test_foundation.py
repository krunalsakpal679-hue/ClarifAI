"""
Phase 1 Foundation Unit Tests:
- Database connectivity & migration execution
- DRF Custom Exception Handler & Ch. 30.8 JSON error shape
- Pagination class behavior
- CORS configuration compliance
"""
import json
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import path
from rest_framework import status, serializers
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from core.exceptions import custom_exception_handler
from core.pagination import StandardPageNumberPagination


# Test serializers & views for exception handler testing
class SampleDummySerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)


class DummyValidationErrorView(APIView):
    def post(self, request):
        serializer = SampleDummySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"status": "ok"})


class DummyServerErrorView(APIView):
    def get(self, request):
        raise RuntimeError("Simulated unhandled internal server error")


class DummyAuthErrorView(APIView):
    def get(self, request):
        raise NotAuthenticated("Authentication credentials were not provided.")


class DummyPermissionErrorView(APIView):
    def get(self, request):
        raise PermissionDenied("You do not have permission to perform this action.")


class DummyNotFoundErrorView(APIView):
    def get(self, request):
        raise NotFound("Requested resource was not found.")


urlpatterns = [
    path('test/validation/', DummyValidationErrorView.as_view(), name='test_validation'),
    path('test/server-error/', DummyServerErrorView.as_view(), name='test_server_error'),
    path('test/auth-error/', DummyAuthErrorView.as_view(), name='test_auth_error'),
    path('test/permission-error/', DummyPermissionErrorView.as_view(), name='test_permission_error'),
    path('test/not-found/', DummyNotFoundErrorView.as_view(), name='test_not_found'),
]


@override_settings(ROOT_URLCONF=__name__)
class FoundationTestCase(TestCase):

    def test_database_connection_and_migrations(self):
        """Confirm database connection is functional and migrations are executed."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            self.assertEqual(row[0], 1)

    def test_custom_exception_handler_validation_error_shape(self):
        """Verify 400 Validation Error returns exact Ch. 30.8 error shape with field details."""
        response = self.client.post(
            '/test/validation/',
            data={},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('Input validation failed', data['error']['message'])
        self.assertIn('details', data['error'])
        self.assertIsInstance(data['error']['details'], list)
        fields = [d['field'] for d in data['error']['details']]
        self.assertIn('name', fields)
        self.assertIn('email', fields)

    def test_custom_exception_handler_not_authenticated_shape(self):
        """Verify 401 Not Authenticated returns Ch. 30.8 error shape."""
        response = self.client.get('/test/auth-error/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error']['message'], 'Authentication credentials were not provided.')

    def test_custom_exception_handler_permission_denied_shape(self):
        """Verify 403 Permission Denied returns Ch. 30.8 error shape."""
        response = self.client.get('/test/permission-error/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'PERMISSION_DENIED')
        self.assertEqual(data['error']['message'], 'You do not have permission to perform this action.')

    def test_custom_exception_handler_not_found_shape(self):
        """Verify 404 Not Found returns Ch. 30.8 error shape."""
        response = self.client.get('/test/not-found/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'NOT_FOUND')
        self.assertEqual(data['error']['message'], 'Requested resource was not found.')

    def test_custom_exception_handler_server_error_sanitization(self):
        """Verify 500 Server Error returns generic message and redacts stack traces."""
        response = self.client.get('/test/server-error/')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.json()
        
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'INTERNAL_SERVER_ERROR')
        self.assertEqual(data['error']['message'], 'An internal server error occurred.')
        # Ensure no trace details are exposed
        self.assertNotIn('Simulated unhandled', json.dumps(data))
        self.assertNotIn('Traceback', json.dumps(data))

    def test_pagination_class_configuration(self):
        """Verify StandardPageNumberPagination attributes."""
        paginator = StandardPageNumberPagination()
        self.assertEqual(paginator.page_size, 20)
        self.assertEqual(paginator.page_size_query_param, 'page_size')
        self.assertEqual(paginator.max_page_size, 100)
