"""
ClarifAI Shared Groq LLM Client Module
Provides unified connection, configuration, timeout, exponential backoff,
secret redaction, and standardized failure classification for Groq Cloud API
(openai/gpt-oss-20b) per PRD v2.3 Chapters 28.1, 28.4, 56.20, and Decision R-08.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from groq import Groq, APIError, APIConnectionError, RateLimitError, NotFoundError, AuthenticationError

logger = logging.getLogger(__name__)

# Default model configuration (openai/gpt-oss-20b) per PRD v2.3 / Decision R-08
DEFAULT_GROQ_MODEL_NAME: str = "openai/gpt-oss-20b"
DEFAULT_TIMEOUT_SECONDS: int = 30
MAX_RETRIES: int = 3

# Versioning tags per AI-MODEL-VERSIONING-INVENTORY-01
PROMPT_VERSION: str = "1.0.0"
SCHEMA_VERSION: str = "1.0.0"

# Standardized PRD Section 56.20 User-Facing Error Message
STANDARD_USER_ERROR_MESSAGE: str = "AI processing is temporarily unavailable. Please try again later."


def get_groq_api_key() -> Optional[str]:
    """
    Retrieves GROQ_API_KEY from environment variables.
    Never hardcoded, never logged.
    """
    return os.getenv("GROQ_API_KEY")


def get_groq_model_name() -> str:
    """
    Retrieves GROQ_MODEL_NAME from environment variables.
    """
    return os.getenv("GROQ_MODEL_NAME", DEFAULT_GROQ_MODEL_NAME)


def get_llm_timeout() -> int:
    """
    Retrieves LLM_REQUEST_TIMEOUT_SECONDS from environment variables.
    """
    try:
        return int(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def sanitize_error_message(error_str: str) -> str:
    """
    Redacts any accidental inclusion of GROQ_API_KEY from error strings before logging.
    """
    key = get_groq_api_key()
    if key and key in error_str:
        error_str = error_str.replace(key, "gsk_***[REDACTED]***")
    return error_str


def get_groq_client(override_api_key: Optional[str] = None, timeout: Optional[int] = None) -> Groq:
    """
    Instantiates and returns a Groq API client.
    Raises ValueError if GROQ_API_KEY is missing.
    """
    api_key = override_api_key or get_groq_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not configured.")
    
    t_out = timeout if timeout is not None else get_llm_timeout()
    return Groq(api_key=api_key, timeout=float(t_out))


def classify_llm_exception(e: Exception) -> Dict[str, Any]:
    """
    Classifies LLM API exceptions into distinct, loggable failure categories
    per PRD v2.3 Section 56.20.
    """
    clean_err = sanitize_error_message(str(e))
    
    if isinstance(e, AuthenticationError):
        category = "AUTH_FAILURE"
        is_transient = False
    elif isinstance(e, NotFoundError):
        category = "MODEL_NOT_FOUND"
        is_transient = False
    elif isinstance(e, RateLimitError):
        category = "QUOTA_OR_RATE_LIMIT_EXHAUSTED"
        is_transient = True
    elif isinstance(e, APIConnectionError):
        category = "NETWORK_CONNECTION_FAILURE"
        is_transient = True
    elif "timeout" in clean_err.lower():
        category = "REQUEST_TIMEOUT"
        is_transient = True
    elif isinstance(e, APIError):
        category = "PROVIDER_API_ERROR"
        is_transient = getattr(e, "status_code", 500) >= 500
    else:
        category = "UNKNOWN_LLM_FAILURE"
        is_transient = False

    return {
        "category": category,
        "is_transient": is_transient,
        "clean_error": clean_err,
        "user_message": STANDARD_USER_ERROR_MESSAGE,
        "approved_fallback_exists": False
    }


def generate_llm_completion(
    prompt: str = "",
    system_prompt: str = "You are a legal contract AI assistant.",
    messages: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.1,
    max_tokens: int = 500,
    override_client: Optional[Groq] = None
) -> Dict[str, Any]:
    """
    Executes a chat completion request against Groq API with exponential backoff retries.
    Supports either single prompt or pre-formatted multi-turn messages array.
    Catches and classifies failures without fabricating outputs or silently substituting models.
    
    Args:
        prompt: User message / structured query prompt (used if messages is None).
        system_prompt: System context instruction (used if messages is None).
        messages: Optional list of message dicts [{"role": "system"/"user"/"assistant", "content": "..."}]
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.
        override_client: Optional Groq client override for testing.
        
    Returns:
        Dict containing generated text or structured error response.
    """
    if messages is None:
        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    elif not messages:
        raise ValueError("Messages list must not be empty.")

    try:
        client = override_client or get_groq_client()
    except Exception as e:
        diag = classify_llm_exception(e)
        logger.error(f"Groq Client Init Error [{diag['category']}]: {diag['clean_error']}")
        raise RuntimeError(f"{STANDARD_USER_ERROR_MESSAGE} ({diag['category']})") from e

    model_name = get_groq_model_name()
    
    t0 = time.time()
    last_classified = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            latency_ms = (time.time() - t0) * 1000
            
            msg = response.choices[0].message
            content = (msg.content or "").strip()
            if not content and getattr(msg, "reasoning", None):
                content = str(msg.reasoning).strip()

            usage_dict = {}
            if getattr(response, "usage", None):
                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }

            return {
                "success": True,
                "content": content,
                "model_name": model_name,
                "latency_ms": round(latency_ms, 2),
                "usage": usage_dict,
                "attempt": attempt,
                "schema_version": SCHEMA_VERSION,
                "prompt_version": PROMPT_VERSION
            }

        except Exception as e:
            classified = classify_llm_exception(e)
            last_classified = classified
            logger.warning(
                f"Groq API Error on attempt {attempt}/{MAX_RETRIES} "
                f"[{classified['category']}]: {classified['clean_error']}"
            )
            
            # Non-transient errors (e.g. 401 Auth or 404 Model Not Found) -> Do not retry
            if not classified["is_transient"] or attempt == MAX_RETRIES:
                break
                
            time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s

    # Final Failure Path: Preserve state, do not fabricate, log safely, raise structured runtime exception
    cat = last_classified["category"] if last_classified else "UNKNOWN"
    err_detail = last_classified["clean_error"] if last_classified else "LLM execution failed"
    logger.error(f"Groq LLM Final Failure [{cat}]: {err_detail}")
    
    raise RuntimeError(f"{STANDARD_USER_ERROR_MESSAGE} ({cat})")


def get_llm_status() -> Dict[str, Any]:
    """
    Returns diagnostic reachability and configuration status of Groq LLM service.
    """
    api_key_set = bool(get_groq_api_key())
    model_name = get_groq_model_name()
    
    if not api_key_set:
        return {
            "configured": False,
            "model_name": model_name,
            "status": "GROQ_API_KEY missing from environment",
            "approved_fallback_exists": False
        }

    try:
        client = get_groq_client()
        models_list = client.models.list()
        accessible_models = [m.id for m in models_list.data]
        is_target_available = model_name in accessible_models
        
        return {
            "configured": True,
            "model_name": model_name,
            "target_model_accessible": is_target_available,
            "available_models_count": len(accessible_models),
            "status": "OPERATIONAL" if is_target_available else "MODEL_ACCESS_WARNING",
            "approved_fallback_exists": False
        }
    except Exception as e:
        diag = classify_llm_exception(e)
        return {
            "configured": True,
            "model_name": model_name,
            "status": "ERROR",
            "error_category": diag["category"],
            "error": diag["clean_error"],
            "user_message": STANDARD_USER_ERROR_MESSAGE,
            "approved_fallback_exists": False
        }
