"""
Smoke test suite for ClarifAI Django service.
"""
from django.test import TestCase
from django.urls import reverse


class ClarifAISmokeTestCase(TestCase):
    def test_health_check_endpoint(self):
        """Verify the API health check endpoint returns 200 OK."""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('service'), 'ClarifAI Django API')
