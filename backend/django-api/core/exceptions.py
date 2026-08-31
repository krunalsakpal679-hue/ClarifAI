"""
Custom DRF exception handler implementing standardized error JSON shape per PRD Ch. 30.8.

Standardized Error Shape:
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error summary",
    "details": [...]  # Optional list of field-level validation errors
  }
}
"""
import logging
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

# Map DRF/Django exception classes to PRD standardized error codes
EXCEPTION_CODE_MAP = {
    ValidationError: "VALIDATION_ERROR",
    NotAuthenticated: "AUTHENTICATION_FAILED",
    AuthenticationFailed: "AUTHENTICATION_FAILED",
    PermissionDenied: "PERMISSION_DENIED",
    DjangoPermissionDenied: "PERMISSION_DENIED",
    NotFound: "NOT_FOUND",
    Http404: "NOT_FOUND",
    MethodNotAllowed: "METHOD_NOT_ALLOWED",
    Throttled: "RATE_LIMITED",
}


def _extract_message_and_details(exc, response_data):
    """
    Extract a clean summary message and optional field-level details from response data.
    """
    if isinstance(exc, ValidationError):
        message = "Input validation failed. Please check payload parameters."
        details = []
        if isinstance(response_data, dict):
            for field, errors in response_data.items():
                if isinstance(errors, list):
                    for err in errors:
                        details.append({"field": str(field), "message": str(err)})
                else:
                    details.append({"field": str(field), "message": str(errors)})
        elif isinstance(response_data, list):
            for err in response_data:
                details.append({"message": str(err)})
        return message, details if details else None

    if isinstance(response_data, dict) and "detail" in response_data:
        return str(response_data["detail"]), None

    if isinstance(response_data, str):
        return response_data, None

    if hasattr(exc, "detail") and isinstance(exc.detail, str):
        return str(exc.detail), None

    return str(exc), None


def custom_exception_handler(exc, context):
    """
    DRF custom exception handler producing exact Ch. 30.8 error shape for all error types.
    """
    # Call DRF's default exception handler first to obtain standard Response
    response = exception_handler(exc, context)

    # Resolve error code from exception type mapping
    error_code = "INTERNAL_SERVER_ERROR"
    for exc_class, code in EXCEPTION_CODE_MAP.items():
        if isinstance(exc, exc_class):
            error_code = code
            break

    if response is not None:
        message, details = _extract_message_and_details(exc, response.data)
        error_payload = {
            "error": {
                "code": error_code,
                "message": message,
            }
        }
        if details:
            error_payload["error"]["details"] = details

        response.data = error_payload
        return response

    # Handle unhandled server exceptions (500 Internal Server Error) safely without leaking stack traces
    logger.exception("Unhandled server exception: %s", exc)
    return Response(
        {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
