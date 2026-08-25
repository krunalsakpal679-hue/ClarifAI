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
    by verifying the X-Internal-Service-Secret header when configured.
    """
    if settings.INTERNAL_SERVICE_SECRET:
        if not x_internal_service_secret or x_internal_service_secret != settings.INTERNAL_SERVICE_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Invalid or missing internal service secret."
            )
    return True
