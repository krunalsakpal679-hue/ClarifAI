"""
Tests for Request/Correlation ID Middleware & Header Propagation.
Traceability: PRD v2.3 Chapter 26.8 (Safe Logging & Observability).
"""
import uuid
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from rest_framework.test import APIClient

from core.middleware import CorrelationIDMiddleware, get_current_correlation_id, set_current_correlation_id
from services.ai_client.client import RealAIClient


class CorrelationIDTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = APIClient()

    def test_middleware_generates_correlation_id_if_missing(self):
        request = self.factory.get('/api/health/')
        middleware = CorrelationIDMiddleware(lambda req: HttpResponse("OK"))
        response = middleware(request)

        self.assertTrue(hasattr(request, 'correlation_id'))
        self.assertIsNotNone(request.correlation_id)
        self.assertEqual(response.headers['X-Correlation-ID'], request.correlation_id)

    def test_middleware_preserves_incoming_correlation_id(self):
        test_cid = str(uuid.uuid4())
        request = self.factory.get('/api/health/', HTTP_X_CORRELATION_ID=test_cid)
        middleware = CorrelationIDMiddleware(lambda req: HttpResponse("OK"))
        response = middleware(request)

        self.assertEqual(request.correlation_id, test_cid)
        self.assertEqual(response.headers['X-Correlation-ID'], test_cid)

    def test_ai_client_forwards_correlation_id_in_headers(self):
        test_cid = str(uuid.uuid4())
        set_current_correlation_id(test_cid)
        try:
            ai_client_inst = RealAIClient()
            headers = ai_client_inst._get_headers()
            self.assertEqual(headers.get('X-Correlation-ID'), test_cid)
        finally:
            set_current_correlation_id(None)
