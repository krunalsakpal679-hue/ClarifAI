"""
ClarifAI FastAPI Microservice Application Assembly
Internal AI inference service invoked exclusively by Django REST API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)

from app.routers.health import router as health_router
from app.routers.risk import router as risk_router
from app.routers.llm import router as llm_router
from app.routers.summarization import router as summarization_router
from app.routers.pdf import router as pdf_router
from app.routers.text_cleaning import router as text_cleaning_router
from app.routers.clause_segmentation import router as clause_segmentation_router
from app.routers.clause_categorization import router as clause_categorization_router
from app.routers.rule_engine import router as rule_engine_router
from app.routers.simplification import router as simplification_router
from app.routers.embedding import router as embedding_router
from app.routers.qdrant import router as qdrant_router
from app.routers.rag import router as rag_router
from app.routers.chatbot import router as chatbot_router

# Initialize structured redacting logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Internal AI microservice for document extraction, risk classification, summarization, RAG chatbot, comparison, and translation.",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None
)

# Register structured global exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include API router modules
app.include_router(health_router)
app.include_router(risk_router)
app.include_router(llm_router)
app.include_router(summarization_router)
app.include_router(pdf_router)
app.include_router(text_cleaning_router)
app.include_router(clause_segmentation_router)
app.include_router(clause_categorization_router)
app.include_router(rule_engine_router)
app.include_router(simplification_router)
app.include_router(embedding_router)
app.include_router(qdrant_router)
app.include_router(rag_router)
app.include_router(chatbot_router)


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "schema_version": settings.SCHEMA_VERSION
    }
