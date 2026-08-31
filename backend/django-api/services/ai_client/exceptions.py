"""
AI Service Adapter Exceptions (PRD Ch. 56.19–56.21, 56.38).
Defines explicit, catchable exception types for internal AI microservice integration.
"""


class AIServiceError(Exception):
    """Base exception for all internal AI Service integration adapter errors."""
    pass


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
    pass


class AIServiceUnavailableError(AIServiceError):
    """Raised on HTTP 500/502/503/504 internal AI service errors or unreachability."""
    pass


class AIServiceValidationError(AIServiceError):
    """
    Raised when AI service response fails schema validation (Ch. 49.3 & Ch. 56.9).
    Rejects malformed outputs, invalid severity enums, or unlisted risk categories.
    """
    pass
