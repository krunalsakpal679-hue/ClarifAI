"""
AI Microservice Integration Adapter Package (PRD Phase 7).
Exposes a unified interface for calling internal AI microservice operations:
- process_document(document_id, file_reference)
- chat(document_id, message, history)
- compare(document_a_id, document_b_id)
- translate(document_id, target_lang, fields)

Controls mock vs real switching via settings.AI_SERVICE_USE_MOCK.
"""
from django.conf import settings
from services.ai_client.client import RealAIClient
from services.ai_client.exceptions import (
    AIServiceConnectionError,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
    AIServiceValidationError,
)
from services.ai_client.mock import MockAIClient


def get_ai_client():
    """
    Factory function returning the active AI Client instance based on settings.AI_SERVICE_USE_MOCK.
    """
    use_mock = getattr(settings, 'AI_SERVICE_USE_MOCK', True)
    if use_mock:
        return MockAIClient()
    return RealAIClient()


def process_document(document_id: str, file_reference: str) -> dict:
    """Wrapper function delegating to active AI Client."""
    client = get_ai_client()
    return client.process_document(document_id, file_reference)


def chat(document_id: str, message: str, history: list = None) -> dict:
    """Wrapper function delegating to active AI Client."""
    client = get_ai_client()
    return client.chat(document_id, message, history=history)


def compare(document_a_id: str, document_b_id: str) -> dict:
    """Wrapper function delegating to active AI Client."""
    client = get_ai_client()
    return client.compare(document_a_id, document_b_id)


def translate(document_id: str, target_lang: str, fields: list = None) -> dict:
    """Wrapper function delegating to active AI Client."""
    client = get_ai_client()
    return client.translate(document_id, target_lang, fields=fields)


def delete_document_embeddings(document_id: str) -> dict:
    """Wrapper function delegating to active AI Client for Qdrant vector cleanup."""
    client = get_ai_client()
    return client.delete_document_embeddings(document_id)


__all__ = [
    'get_ai_client',
    'process_document',
    'chat',
    'compare',
    'translate',
    'delete_document_embeddings',
    'MockAIClient',
    'RealAIClient',
    'AIServiceError',
    'AIServiceConnectionError',
    'AIServiceTimeoutError',
    'AIServiceRateLimitError',
    'AIServiceUnavailableError',
    'AIServiceValidationError',
]

