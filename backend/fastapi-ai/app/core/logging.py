"""
ClarifAI FastAPI Core Logging Module
Configures structured logging and enforces secret/content redaction per security directives.
"""

import logging
import sys
from typing import Any
from app.core.config import settings


class SecretRedactingFormatter(logging.Formatter):
    """
    Custom log formatter that automatically redacts API keys and secrets from log output.
    """
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        
        # Redact Groq API Key if configured
        if settings.GROQ_API_KEY and settings.GROQ_API_KEY in formatted:
            formatted = formatted.replace(settings.GROQ_API_KEY, "gsk_***[REDACTED]***")
            
        # Redact Qdrant API Key if configured
        if settings.QDRANT_API_KEY and settings.QDRANT_API_KEY in formatted:
            formatted = formatted.replace(settings.QDRANT_API_KEY, "***[REDACTED_QDRANT_KEY]***")

        # Redact Internal Secret Header Token
        if settings.INTERNAL_SERVICE_SECRET and settings.INTERNAL_SERVICE_SECRET in formatted:
            formatted = formatted.replace(settings.INTERNAL_SERVICE_SECRET, "***[REDACTED_INTERNAL_SECRET]***")

        return formatted


def setup_logging():
    """
    Configures stream logging to stdout with SecretRedactingFormatter.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

    # Clear pre-existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = SecretRedactingFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Silence verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("torch").setLevel(logging.ERROR)


logger = logging.getLogger("clarifai-ai")
