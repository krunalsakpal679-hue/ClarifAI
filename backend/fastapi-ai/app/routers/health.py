"""
ClarifAI Health API Router
"""

from fastapi import APIRouter
from app.core.config import settings
from app.services.ocr_service import get_tesseract_status
from app.services.embedding_service import get_embedding_status
from app.services.risk_service import get_legal_bert_status
from app.services.llm_client import get_llm_status
from app.services.summarization_service import get_summarization_status
from app.models.health import HealthStatusResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthStatusResponse)
async def health_check():
    """
    Main health check endpoint returning { status: 'ok' } and diagnostic metadata.
    """
    tesseract_info = get_tesseract_status()
    embedding_info = get_embedding_status()
    legal_bert_info = get_legal_bert_status()
    llm_info = get_llm_status()
    summarization_info = get_summarization_status()

    is_healthy = (
        tesseract_info.get("installed", False) and
        embedding_info.get("loaded", False) and
        legal_bert_info.get("loaded", False) and
        llm_info.get("configured", False) and
        summarization_info.get("loaded", False)
    )

    return HealthStatusResponse(
        status="ok" if is_healthy else "degraded",
        service="fastapi-ai",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        groq_configured=bool(settings.GROQ_API_KEY),
        qdrant_configured=bool(settings.QDRANT_URL),
        tesseract=tesseract_info,
        embedding=embedding_info,
        legal_bert=legal_bert_info,
        llm=llm_info,
        summarization=summarization_info,
        schema_version=settings.SCHEMA_VERSION
    )


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes / Docker liveness probe endpoint.
    """
    return {"status": "alive", "service": "fastapi-ai"}


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes / Docker readiness probe endpoint.
    """
    return {
        "status": "ready",
        "service": "fastapi-ai",
        "groq_configured": bool(settings.GROQ_API_KEY)
    }


@router.get("/health/llm")
async def llm_health_check():
    """
    Full Groq LLM diagnostic health endpoint per Section 1 requirements.
    Never exposes raw key, returns redacted prefix and active mode.
    """
    raw_key = (settings.GROQ_API_KEY or "").strip()
    key_len = len(raw_key)
    prefix = raw_key[:4] if raw_key else ""
    redacted = f"{prefix}***[REDACTED]***" if (raw_key and raw_key.startswith("gsk_")) else "NOT_CONFIGURED"
    
    llm_info = get_llm_status()
    active_mode = "LLM mode" if bool(raw_key) else "Limited mode (LLM unavailable)"
    
    return {
        "status": "ok" if llm_info.get("configured") else "limited",
        "mode": active_mode,
        "model_name": settings.GROQ_MODEL_NAME,
        "key_configured": bool(raw_key),
        "key_redacted": redacted,
        "key_length": key_len,
        "diagnostics": llm_info
    }
