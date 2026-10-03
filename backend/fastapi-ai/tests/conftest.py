import pytest
from app.core.config import settings

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """
    Autouse fixture for pytest:
    Sets ENVIRONMENT to 'test' and clears INTERNAL_SERVICE_SECRET
    so TestClient endpoint calls pass authorization without needing explicit headers.
    """
    monkeypatch.setattr(settings, "INTERNAL_SERVICE_SECRET", "")
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
