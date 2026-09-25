"""
Smoke test suite for ClarifAI Django service.
"""
from django.test import TestCase
from django.urls import reverse


class ClarifAISmokeTestCase(TestCase):
    def test_health_check_endpoint(self):
        """Verify the API health check endpoint returns 200 OK when DB is healthy."""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('service'), 'ClarifAI Django API')

    def test_health_check_endpoint_db_failure(self):
        """Verify the API health check endpoint returns 503 when DB is unreachable."""
        from unittest.mock import patch
        from django.db import DatabaseError
        with patch('django.db.connection.cursor', side_effect=DatabaseError('Connection refused')):
            response = self.client.get(reverse('health_check'))
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data.get('status'), 'unhealthy')
            self.assertEqual(data.get('database'), 'disconnected')
