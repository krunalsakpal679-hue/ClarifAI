# ClarifAI AI Microservice Architecture Foundation (`AI-PHASE-01-FASTAPI-FOUNDATION`)

**Service:** `/backend/fastapi-ai`  
**Role:** AI Pipeline Developer (Developer 3)  
**Project:** ClarifAI  
**Source Specification:** ClarifAI PRD v2.3 (Chapters 28.1, 50, Section 56.20)  
**Date:** August 23, 2026  
**Status:** Completed  

---

## 1. Executive Summary

This document establishes the official architectural foundation, application skeleton, module layout, security isolation, logging policies, and model initialization strategy for the `/backend/fastapi-ai` microservice in ClarifAI per PRD v2.3 Chapter 28.1.

---

## 2. Module Layout & Project Structure

The `/backend/fastapi-ai` service adheres to a modular, domain-driven package structure:

```
/backend/fastapi-ai
├── app/
│   ├── main.py                  # Application entrypoint & global assembly
│   ├── core/
│   │   ├── config.py            # Environment-driven settings (pydantic-settings)
│   │   ├── logging.py           # Redacting logger & stdout stream formatter
│   │   ├── security.py          # Internal secret header validation dependency
│   │   └── exceptions.py        # Global exception handlers & uniform JSON error shape
│   ├── models/                  # Pydantic request/response schemas
│   │   ├── common.py            # ErrorDetail, ErrorResponse, SCHEMA_VERSION="1.0.0"
│   │   ├── health.py            # HealthStatusResponse, ComponentHealth
│   │   ├── risk.py              # ClauseRiskRequest, ClauseRiskResponse
│   │   ├── llm.py               # LLMCompletionRequest, LLMCompletionResponse
│   │   └── summarization.py     # SummarizationRequest, SummarizationResponse
│   ├── routers/                 # API Endpoint Controllers
│   │   ├── health.py            # GET /health, /health/live, /health/ready
│   │   ├── risk.py              # POST /api/v1/classify-risk
│   │   ├── llm.py               # POST /api/v1/llm-completion
│   │   └── summarization.py     # POST /api/v1/summarize
│   └── services/                # Model inference & integration services
│       ├── ocr_service.py       # Tesseract OCR service
│       ├── embedding_service.py # Multilingual-E5 embedding service
│       ├── risk_service.py      # Legal-BERT risk classification service
│       ├── llm_client.py        # Groq Cloud LLM shared client
│       └── summarization_service.py # BART-base summarization service
├── tests/                       # Pytest unit test suites
│   ├── test_foundation.py       # Skeleton, health, error shape, and security tests
│   ├── test_failure_handling.py # Failure classification & secret redaction tests
│   ├── test_legal_bert.py       # Legal-BERT risk classification tests
│   ├── test_llm.py              # Groq LLM client tests
│   ├── test_summarization.py    # BART summarization tests
│   ├── test_embedding.py        # Multilingual-E5 embedding tests
│   └── test_ocr.py              # Tesseract OCR tests
├── Dockerfile                   # Python 3.11-slim container definition
├── requirements.txt             # Pinned Python library dependencies
└── .env.example                 # Environment configuration template
```

---

## 3. Model Initialization Strategy

### Strategy Chosen: **Lazy-Load-On-First-Use with Singleton Caching**

* **Rationale:**
  1. *Fast Application Boot:* Allows the FastAPI microservice container to start instantly (< 1.5 seconds) and pass health probes immediately.
  2. *Resource Conservation:* Prevents loading all 5 model weights simultaneously into memory during service boot, preventing CUDA OOM or RAM exhaustion.
  3. *Fault Tolerance:* If an external model hub or vector store is slow during boot, service startup is not blocked.

* **Implementation Pattern:**
  Each service module (`risk_service.py`, `embedding_service.py`, `summarization_service.py`, `llm_client.py`) maintains thread-safe module-level singleton instances (`_model_instance = None`). When an endpoint receives its first inference request, `load_model()` instantiates the weights, caches the singleton, and reuses it for all subsequent requests.

---

## 4. Network Isolation & Security Architecture

### Public vs. Internal Exposure

* **Internal Service Isolation:** `/backend/fastapi-ai` is an **internal microservice**. It is never exposed directly to the public internet or the frontend SPA.
* **Network Execution Boundary:** Accessible only via the internal Docker container network (`clarifai_backend_net`) or local loopback (`127.0.0.1:8000`) invoked exclusively by the Django REST API backend.
* **Authentication Header:** Endpoints enforce internal header token verification via `app/core/security.py`:
  `X-Internal-Service-Secret: <INTERNAL_SERVICE_SECRET>`

---

## 5. Structured JSON Error Response Conventions

All API controllers and exception handlers emit a standardized JSON error shape per PRD Section 56.20:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed. Please check payload parameters.",
    "details": [
      {
        "field": "clause_text",
        "message": "Field required"
      }
    ]
  },
  "schema_version": "1.0.0"
}
```

* **User-Facing Generic Message for Server Failures (PRD Section 56.20):**
  `"AI processing is temporarily unavailable. Please try again later."`

---

## 6. Secret Redaction & Logging Guidelines

* **Redaction Formatter (`SecretRedactingFormatter`):** Custom log formatter in `app/core/logging.py` automatically scrubs `GROQ_API_KEY`, `QDRANT_API_KEY`, and `INTERNAL_SERVICE_SECRET` from all log lines before writing to stdout.
* **Zero Document Logging:** Raw contract text and document contents are strictly excluded from log statements; only token counts, clause counts, stage status, and latency metrics are logged.
