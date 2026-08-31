"""
Phase 3 Authorization & IDOR Protection Unit Tests:
- Tests IsOwner permission class
- Asserts 404-not-403 IDOR security posture (PRD Ch. 26.2, 27, 30.8)
- Tests IDORTestMixin reusable test utility
"""
import uuid
from django.contrib.auth import get_user_model
from django.db import models
from django.test import TestCase, override_settings
from django.urls import path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwner
from core.testing import IDORTestMixin

User = get_user_model()


# Temporary in-memory / dummy resource representation for testing IsOwner permission
class DummyProtectedResource:
    """
    Dummy resource with UUID primary key and owner field.
    Binding Architecture Rule: All future resource models MUST use UUIDs as PKs.
    """
    def __init__(self, owner, resource_id=None):
        self.id = resource_id or uuid.uuid4()
        self.owner = owner


# Global in-memory storage for dummy test objects
TEST_RESOURCES = {}


class DummyDetailView(APIView):
    """
    Dummy Detail View enforcing IsOwner permission.
    """
    permission_classes = [IsOwner]

    def get(self, request, pk):
        resource = TEST_RESOURCES.get(str(pk))
        if not resource:
            from rest_framework.exceptions import NotFound
            raise NotFound("Requested resource was not found.")

        # Check object-level permission
        self.check_object_permissions(request, resource)

        return Response({
            "id": str(resource.id),
            "owner": resource.owner.email,
            "data": "Protected secret content"
        })


urlpatterns = [
    path('test/resource/<uuid:pk>/', DummyDetailView.as_view(), name='dummy_resource_detail'),
]


@override_settings(ROOT_URLCONF=__name__)
class AuthorizationTestCase(TestCase, IDORTestMixin):

    def setUp(self):
        TEST_RESOURCES.clear()
        self.create_two_users()

        # Create dummy resource owned by user_a
        self.resource_a = DummyProtectedResource(owner=self.user_a)
        TEST_RESOURCES[str(self.resource_a.id)] = self.resource_a
        self.resource_url = f'/test/resource/{self.resource_a.id}/'

    def tearDown(self):
        TEST_RESOURCES.clear()

    def test_owner_can_access_own_resource(self):
        """Owner accessing their own resource receives HTTP 200 OK."""
        response = self.client.get(
            self.resource_url,
            **self.auth_headers_a
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], str(self.resource_a.id))
        self.assertEqual(data['owner'], self.user_a.email)

    def test_non_owner_receives_404_not_403_idor_protection(self):
        """Non-owner accessing existing resource receives HTTP 404 NOT FOUND, NEVER 403 FORBIDDEN."""
        # Use IDORTestMixin helper
        response = self.assert_idor_protection(
            client=self.client,
            resource_url=self.resource_url,
            method='get'
        )

        # Double-check explicit status assertions
        self.assertNotEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "SECURITY FAILURE: Non-owner access returned 403 Forbidden instead of masking resource existence with 404 Not Found!"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Confirm exact Ch. 30.8 error shape
        data = response.json()
        self.assertEqual(data['error']['code'], 'NOT_FOUND')

    def test_unauthenticated_user_access_denied(self):
        """Unauthenticated user receives HTTP 401 AUTHENTICATION_FAILED."""
        response = self.client.get(self.resource_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertEqual(data['error']['code'], 'AUTHENTICATION_FAILED')

    def test_uuid_primary_key_binding_rule_compliance(self):
        """Verify dummy resource ID is a valid UUID per binding architecture rule."""
        self.assertIsInstance(self.resource_a.id, uuid.UUID)
