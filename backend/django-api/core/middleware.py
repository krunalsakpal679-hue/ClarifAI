"""
ClarifAI Django API Middleware Module
Implements Correlation / Request ID tracking across HTTP and async task contexts.
"""
import threading
import uuid

_thread_locals = threading.local()


def get_current_correlation_id() -> str:
    """Retrieve the current thread's correlation ID, if set."""
    return getattr(_thread_locals, 'correlation_id', None)


def set_current_correlation_id(correlation_id: str):
    """Set the current thread's correlation ID."""
    _thread_locals.correlation_id = correlation_id


class CorrelationIDMiddleware:
    """
    Middleware that extracts or generates an X-Correlation-ID header for every request,
    stores it in thread-local context, and propagates it in the HTTP response headers.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID') or str(uuid.uuid4())
        request.correlation_id = correlation_id
        set_current_correlation_id(correlation_id)

        try:
            response = self.get_response(request)
            response['X-Correlation-ID'] = correlation_id
            return response
        finally:
            set_current_correlation_id(None)
