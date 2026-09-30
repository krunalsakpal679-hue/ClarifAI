"""
ClarifAI FastAPI Security Dependency Module
Enforces internal network service authentication via header validation.
"""

from fastapi import Header, HTTPException, status
from typing import Optional
from app.core.config import settings


async def verify_internal_secret(
    x_internal_service_secret: Optional[str] = Header(None, alias="X-Internal-Service-Secret")
):
    """
    Validates that the incoming HTTP request originates from the internal Django backend
    by verifying the X-Internal-Service-Secret header.

    Security Gating Policy:
    - In non-development/non-test environments, INTERNAL_SERVICE_SECRET must be set and requests
      missing or having an incorrect secret header are strictly rejected (HTTP 403 Forbidden).
    - If INTERNAL_SERVICE_SECRET is configured in any environment, matching is strictly enforced.
    - In explicit development/test environments (ENVIRONMENT in ['development', 'dev', 'test', 'testing', 'local']),
      if INTERNAL_SERVICE_SECRET is unset, requests are permitted for local development convenience.
    """
    is_dev_env = settings.ENVIRONMENT.lower() in ["development", "dev", "test", "testing", "local"]

    if not settings.INTERNAL_SERVICE_SECRET:
        if not is_dev_env:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. INTERNAL_SERVICE_SECRET must be configured in production."
            )
        return True

    if not x_internal_service_secret or x_internal_service_secret != settings.INTERNAL_SERVICE_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Invalid or missing internal service secret."
        )
    return True

