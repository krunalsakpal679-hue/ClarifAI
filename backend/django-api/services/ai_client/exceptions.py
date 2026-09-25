from rest_framework import status
from rest_framework.exceptions import APIException


class AIServiceError(APIException):
    """Base exception for all internal AI Service integration adapter errors."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "AI service is currently unavailable. Please try again later."
    default_code = "AI_SERVICE_UNAVAILABLE"


class AIServiceConnectionError(AIServiceError):
    """Raised when HTTP connection fails or network drops after single retry."""
    pass


class AIServiceTimeoutError(AIServiceError):
    """Raised when internal AI service request times out."""
    pass


class AIServiceRateLimitError(AIServiceError):
    """
    Raised on HTTP 429 Too Many Requests (Rate limit or Free-tier quota exhaustion per Ch. 56.19).
    Never silently converts failure to default output or silent model fallback.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = "RATE_LIMITED"


class AIServiceUnavailableError(AIServiceError):
    """Raised on HTTP 500/502/503/504 internal AI service errors or unreachability."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "AI_SERVICE_UNAVAILABLE"


class AIServiceValidationError(AIServiceError):
    """
    Raised when AI service response fails schema validation (Ch. 49.3 & Ch. 56.9).
    Rejects malformed outputs, invalid severity enums, or unlisted risk categories.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "AI_SERVICE_UNAVAILABLE"

