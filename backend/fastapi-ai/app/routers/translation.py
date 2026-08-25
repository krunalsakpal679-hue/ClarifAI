"""
FastAPI Router for Multilingual English-to-Hindi Translation Service (AI-PHASE-MULTILINGUAL)
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from app.models.translation import TranslationRequest, TranslationResponse
from app.services.translation_service import translate_document_analysis
from app.core.security import verify_internal_secret

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/translation", tags=["Multilingual Translation Engine"])


@router.post(
    "/translate-document",
    response_model=TranslationResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Translate AI document analysis (summary & simplified clauses) to Hindi",
    description="Translates summary and clause fields to Hindi while keeping original_text 100% unaltered. Enforces per-document failure isolation."
)
async def translate_document_endpoint(request: TranslationRequest):
    try:
        res = translate_document_analysis(
            user_id=request.user_id,
            document_id=request.document_id,
            summary=request.summary,
            clauses=request.clauses,
            target_language=request.target_language or "hi"
        )
        return TranslationResponse(**res)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Internal error during document translation endpoint execution: {exc}")
        raise HTTPException(status_code=500, detail=f"Document translation execution failed: {exc}")
