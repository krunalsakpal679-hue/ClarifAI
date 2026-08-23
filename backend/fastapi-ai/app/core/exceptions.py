"""
ClarifAI Structured Global Exception Handlers
Enforces consistent JSON error payload shape across all FastAPI routes.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

SCHEMA_VERSION: str = "1.0.0"
STANDARD_USER_ERROR_MESSAGE: str = "AI processing is temporarily unavailable. Please try again later."


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handles standard FastAPI/Starlette HTTPExceptions and returns uniform JSON shape.
    """
    status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    raw_detail = getattr(exc, "detail", str(exc))

    if isinstance(raw_detail, dict):
        error_code = raw_detail.get("code", f"HTTP_{status_code}")
        error_message = raw_detail.get("message", "An error occurred during request processing.")
        error_details = raw_detail.get("details", None)
    else:
        error_code = f"HTTP_{status_code}"
        error_message = str(raw_detail)
        error_details = None

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": error_message,
                "details": error_details
            },
            "schema_version": SCHEMA_VERSION
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handles Pydantic validation errors (HTTP 422) and returns uniform JSON shape.
    """
    errors_list = []
    for err in exc.errors():
        loc_str = " -> ".join([str(x) for x in err.get("loc", [])])
        errors_list.append({
            "field": loc_str,
            "message": err.get("msg", "Invalid field value")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check payload parameters.",
                "details": errors_list
            },
            "schema_version": SCHEMA_VERSION
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all unhandled server exceptions (HTTP 500) and returns safe, structured JSON.
    Prevents secret or document leakage while emitting PRD Section 56.20 user-facing message.
    """
    logger.error(f"Unhandled Microservice Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": STANDARD_USER_ERROR_MESSAGE,
                "details": str(exc) if not hasattr(exc, "args") else str(exc.args[0]) if exc.args else "Internal error"
            },
            "schema_version": SCHEMA_VERSION
        }
    )
