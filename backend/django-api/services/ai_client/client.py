"""
Real HTTP AI Client Implementation (PRD Phase 7).
HTTP client communicating with internal FastAPI microservice.

NOTE: Exact internal route paths (/api/v1/process-document, /api/v1/chat, etc.) are explicitly
classified as an Engineering Implementation Detail (Classification E) to be finalized with the AI Developer.
"""
import logging
import requests
from django.conf import settings

from services.ai_client.exceptions import (
    AIServiceConnectionError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
)
from services.ai_client.validators import (
    validate_chat_response,
    validate_compare_response,
    validate_process_document_response,
    validate_translate_response,
)

logger = logging.getLogger(__name__)


class RealAIClient:
    """
    HTTP Client for calling the internal FastAPI AI microservice.
    Enforces timeout, single network-level retry, strict response validation,
    and category-specific exception mapping per PRD Ch. 56.19–56.21.
    """

    def __init__(self, base_url: str = None, secret: str = None, timeout: int = None):
        self.base_url = (base_url or getattr(settings, 'AI_SERVICE_BASE_URL', 'http://localhost:8001')).rstrip('/')
        self.secret = secret or getattr(settings, 'AI_SERVICE_SECRET', '')
        self.timeout = timeout or getattr(settings, 'AI_SERVICE_TIMEOUT', 30)

    def _get_headers(self) -> dict:
        headers = {'Content-Type': 'application/json'}

        if self.secret:
            headers['X-Internal-Secret'] = self.secret
        return headers

    def _send_request(self, method: str, endpoint: str, json_data: dict = None) -> dict:
        """
        Sends HTTP request to internal FastAPI microservice.
        
        Retry Policy:
        - Network Connection drops/failures: Exactly 1 single retry attempt.
        - HTTP 4xx / 5xx status codes & AI-logic errors: ZERO retries (fails immediately).
        """
        # Engineering Implementation Detail (Classification E): Endpoint path format
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        response = None
        for attempt in range(2):  # Initial attempt + 1 single retry on network drop
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=json_data,
                    headers=headers,
                    timeout=self.timeout
                )
                break  # Request succeeded at HTTP transport level
            except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as net_exc:
                if attempt == 0:
                    logger.warning(f"Network error calling AI service at {url}. Retrying once: {net_exc}")
                    continue
                logger.error(f"Network connection to AI service failed after 1 retry: {net_exc}")
                raise AIServiceConnectionError(f"Network connection to AI service failed: {net_exc}") from net_exc
            except requests.exceptions.Timeout as timeout_exc:
                # Timeout is not retried to avoid compounding latency (PRD Ch. 33.12)
                logger.error(f"AI service request timed out after {self.timeout}s: {timeout_exc}")
                raise AIServiceTimeoutError(f"AI service request timed out after {self.timeout}s.") from timeout_exc
            except requests.exceptions.RequestException as req_exc:
                logger.error(f"HTTP request exception calling AI service: {req_exc}")
                raise AIServiceConnectionError(f"HTTP request error: {req_exc}") from req_exc

        if response is None:
            raise AIServiceConnectionError("No response received from AI microservice.")

        # HTTP Status Code to Exception Mapping (PRD Ch. 56.19)
        if response.status_code == 429:
            logger.error("AI microservice returned HTTP 429 Rate Limit / Free-tier quota exhaustion.")
            raise AIServiceRateLimitError("AI microservice rate limit or free-tier quota exhausted (HTTP 429).")
        elif response.status_code in (500, 502, 503, 504):
            logger.error(f"AI microservice server error (HTTP {response.status_code}): {response.text}")
            raise AIServiceUnavailableError(f"AI microservice unavailable (HTTP {response.status_code}).")
        elif response.status_code >= 400:
            logger.error(f"AI microservice client error (HTTP {response.status_code}): {response.text}")
            raise AIServiceUnavailableError(f"AI microservice error (HTTP {response.status_code}).")

        try:
            return response.json()
        except ValueError as json_exc:
            logger.error(f"Invalid JSON returned by AI microservice: {json_exc}")
            raise AIServiceUnavailableError("Invalid non-JSON response from AI microservice.") from json_exc

    def process_document(self, document_id: str, file_reference: str) -> dict:
        """
        Invokes document processing pipeline on internal FastAPI AI microservice.
        Classification E: Internal route path pending final contract confirmation.
        """
        payload = {
            "document_id": str(document_id),
            "file_reference": str(file_reference)
        }
        # Engineering Implementation Detail (Classification E)
        raw_response = self._send_request("POST", "/api/v1/process-document", json_data=payload)
        return validate_process_document_response(raw_response)

    def chat(self, document_id: str, message: str, history: list = None) -> dict:
        """
        Invokes RAG Chat query on internal FastAPI AI microservice.
        Classification E: Internal route path pending final contract confirmation.
        """
        payload = {
            "document_id": str(document_id),
            "message": str(message),
            "history": history or []
        }
        # Engineering Implementation Detail (Classification E)
        raw_response = self._send_request("POST", "/api/v1/chat", json_data=payload)
        return validate_chat_response(raw_response)

    def compare(self, document_a_id: str, document_b_id: str) -> dict:
        """
        Invokes document comparison on internal FastAPI AI microservice.
        Classification E: Internal route path pending final contract confirmation.
        """
        payload = {
            "document_a_id": str(document_a_id),
            "document_b_id": str(document_b_id)
        }
        # Engineering Implementation Detail (Classification E)
        raw_response = self._send_request("POST", "/api/v1/compare", json_data=payload)
        return validate_compare_response(raw_response)

    def translate(self, document_id: str, target_lang: str, fields: list = None) -> dict:
        """
        Invokes document translation on internal FastAPI AI microservice.
        Classification E: Internal route path pending final contract confirmation.
        """
        payload = {
            "document_id": str(document_id),
            "target_lang": str(target_lang),
            "fields": fields or []
        }
        # Engineering Implementation Detail (Classification E)
        raw_response = self._send_request("POST", "/api/v1/translate", json_data=payload)
        return validate_translate_response(raw_response)
