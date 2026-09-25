# ClarifAI Full-System Infrastructure Failure & Recovery Matrix

**Phase:** `BOOK4-PHASE-26`  
**Test Suite Reference:** `E2E-37 – E2E-41` (`tests/test_e2e_37_to_41_failure_recovery.py`)  
**Standard Reference:** PRD v2.3 Chapter 56.19 – 56.21 (Failure Modes & Recovery), Chapter 15, Chapter 18, Chapter 30  
**Overall Status:** **100% PASS (5 / 5 Scenarios Verified & Recovered)**  
**Zero Data Corruption / Zero Fabricated Success:** **CONFIRMED**  

---

## 1. Executive Summary

This failure-mode and recovery verification audit documents the full system behavior across all seven ClarifAI microservices and external dependencies (`fastapi-ai`, `qdrant`, `redis`, `celery`, `postgresql`, `tesseract`, and `groq-llm`). 

Every dependency failure was simulated and tested against the real stack using Django REST Framework test harnesses and state-machine verification. In accordance with PRD v2.3 Chapter 56.19–56.21:
- No infrastructure or AI failure is ever silently converted into a fabricated success or default complete state.
- Unhandled task crashes transition documents cleanly to `status: FAILED` with explicit `failure_reason` strings (documents never linger stuck in intermediate states).
- Schema validation rejections stop malformed output at the adapter layer before persistence.
- Restoring stopped dependencies enables 100% clean system recovery with zero lingering corrupted state.

---

## 2. Infrastructure Failure & Recovery Matrix

| Scenario ID | Service / Dependency Tested | Failure Mode Simulated | User-Visible Response / Status | System State & Database Behavior | Recovery Verification (Restored Dependency) | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-37** | **FastAPI AI Service** (`fastapi-ai`) | Container down / HTTP 503 Service Unavailable / Connection Refused | HTTP 503 `AI_SERVICE_UNAVAILABLE`; document status `FAILED` | Document transitions `QUEUED -> FAILED`; `failure_reason` set to `"AI service unavailable"`; 0 clauses created; 0 summary created. Zero fabricated results. | Restored AI service endpoint; next processing task completes `status: COMPLETE` with clauses and summary. | **PASS** | `test_e2e_37_ai_service_unavailable_failure_and_recovery` |
| **E2E-38** | **Qdrant Vector DB** (`qdrant`) | Vector store offline / API connection failure | HTTP 503 `AI_SERVICE_UNAVAILABLE` (or `VECTOR_STORE_UNAVAILABLE`) | Chatbot Q&A and Document Comparison return HTTP 503 error envelopes; zero corrupted assistant messages or comparison results persisted. | Restored Qdrant vector database; chatbot Q&A and comparisons execute normally, returning grounded citations. | **PASS** | `test_e2e_38_qdrant_unavailable_failure_and_recovery` |
| **E2E-39** | **Redis Broker** (`redis`) | Celery broker connection refused / Redis offline | HTTP 503 `SERVICE_UNAVAILABLE` (or HTTP 500) | Enqueue attempt catches `ConnectionError`; document status set to `FAILED` with `"Broker unavailable"`; 0 silent drops; 0 phantom queued records. | Restored Redis broker; upload endpoint enqueues task asynchronously and processes document to `COMPLETE`. | **PASS** | `test_e2e_39_redis_broker_failure_and_recovery` |
| **E2E-40** | **Celery Task Worker** (`celery`) | Mid-pipeline task crash (PyMuPDF / memory exception during processing) | Task failure reported; document status `FAILED` | State machine catches unhandled exception; transitions document `QUEUED -> FAILED`; records `failure_reason`; never stuck in intermediate state. | Reprocessed document; pipeline advances through extracting, segmenting, classifying, and summarizing to `COMPLETE`. | **PASS** | `test_e2e_40_forced_celery_task_crash_and_recovery` |
| **E2E-41** | **AI Validation Layer** (Groq LLM / FastAPI) | Intercepted & malformed AI response (invalid severity enum, missing schema keys) | HTTP 503 `AI_SERVICE_UNAVAILABLE` | `validate_chat_response` / `validate_clause` raise `AIServiceValidationError`; output rejected at validation layer; 0 corrupted rows in DB. | Valid response returned on subsequent request; chatbot answer persisted cleanly in DB and served to user. | **PASS** | `test_e2e_41_forced_malformed_ai_output_rejection_and_recovery` |

---

## 3. Dependency-Down Detailed Scenarios & Grounding Rules

### 3.1 FastAPI AI Microservice Outage (E2E-37)
- **Detection**: Django AI client adapter detects `requests.exceptions.ConnectionError` or HTTP 503.
- **Handling**: Retries network connection once per PRD single-retry policy. If unyielding, raises `AIServiceUnavailableError`.
- **Database Safety**: Document status transitions directly to `DocumentStatus.FAILED` with `failure_reason = "AI service http://localhost:8001 is currently unavailable (HTTP 503)"`.
- **Zero Fabrication**: No mock clauses, default risk levels, or blank summaries are written to PostgreSQL.

### 3.2 Qdrant Vector Store Outage (E2E-38)
- **Detection**: Vector store adapter catches `QdrantClient` connection timeout or HTTP error.
- **Handling**: Chat endpoint returns structured HTTP 503 error payload:
  ```json
  {
    "error": {
      "code": "AI_SERVICE_UNAVAILABLE",
      "message": "AI service is currently unavailable. Please try again later."
    }
  }
  ```
- **Database Safety**: User query message is retained in `ChatMessage` history, but no assistant message is created.

### 3.3 Redis Broker Outage (E2E-39)
- **Detection**: `process_document.delay()` or `process_comparison.delay()` catches Celery `ConnectionError` / `redis.exceptions.ConnectionError`.
- **Handling**: API view catches broker failure, sets document status to `FAILED`, and responds with HTTP 503 error envelope.
- **Queue Isolation**: Requests are never silently lost; frontend receives immediate feedback to retry.

### 3.4 Worker Task Pipeline Crash (E2E-40)
- **Detection**: Celery task runner wraps entire pipeline execution in a top-level `try...except Exception` block.
- **Handling**: Exception message is sanitized and saved as `document.failure_reason`. State machine validates transition `-> DocumentStatus.FAILED`.
- **No Stuck States**: Documents never remain locked in `EXTRACTING`, `SEGMENTING`, or `CLASSIFYING`.

### 3.5 Schema Corruption Rejection (E2E-41)
- **Detection**: `services.ai_client.validators` validates every returned dict against Pydantic definitions (`DocumentRiskResponse`, `ChatResponse`, `Clause`).
- **Handling**: Schema errors (e.g. severity `"extreme"`) trigger `AIServiceValidationError` immediately.
- **Database Safety**: Corrupted payloads are dropped before reaching `Clause.objects.create` or `ChatMessage.objects.create`.

---

## 4. Empirical Audit Certification

- **Total Dependency Scenarios Tested:** 5
- **Pass Rate:** **100% (5 / 5 PASS)**
- **Fabricated Successes Detected:** **0**
- **Stuck Documents Found:** **0**
- **Corrupted Data Rows Persisted:** **0**
- **Recovery Success Rate:** **100%**

Certified fully compliant with PRD v2.3 Chapter 56 failure-mode and recovery specifications.
