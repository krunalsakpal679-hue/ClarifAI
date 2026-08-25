"""
ClarifAI FastAPI Microservice Foundation Unit Tests (AI-PHASE-01-FASTAPI-FOUNDATION)
Verifies module layout, GET /health response, structured error payloads, logging redaction,
and internal security middleware.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.logging import SecretRedactingFormatter
import logging

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ClarifAI AI Microservice"
    assert data["status"] == "running"
    assert data["schema_version"] == "1.0.0"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "healthy", "degraded"]
    assert data["service"] == "fastapi-ai"
    assert "groq_configured" in data
    assert "qdrant_configured" in data
    assert data["schema_version"] == "1.0.0"


def test_health_liveness_and_readiness():
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_structured_error_on_404_route():
    response = client.get("/non-existent-endpoint-path")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "HTTP_404"
    assert data["schema_version"] == "1.0.0"


def test_structured_error_on_validation_failure():
    # Missing required 'clause_text' field
    response = client.post("/api/v1/classify-risk", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0
    assert data["schema_version"] == "1.0.0"


def test_secret_redacting_formatter():
    formatter = SecretRedactingFormatter("%(message)s")
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Connecting to Groq with key gsk_test123456789key", args=(), exc_info=None
    )
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "GROQ_API_KEY", "gsk_test123456789key")
        formatted = formatter.format(record)
        assert "gsk_test123456789key" not in formatted
        assert "gsk_***[REDACTED]***" in formatted


def test_internal_security_header_denial():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "INTERNAL_SERVICE_SECRET", "super-secret-internal-token-123")
        
        # Missing secret header -> HTTP 403
        res_no_header = client.post("/api/v1/classify-risk", json={"clause_text": "Sample clause"})
        assert res_no_header.status_code == 403
        assert res_no_header.json()["success"] is False
        
        # Correct secret header -> HTTP 200
        headers = {"X-Internal-Service-Secret": "super-secret-internal-token-123"}
        res_valid = client.post("/api/v1/classify-risk", json={"clause_text": "Sample clause"}, headers=headers)
        assert res_valid.status_code == 200
        assert res_valid.json()["success"] is True
