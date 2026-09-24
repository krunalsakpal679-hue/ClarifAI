# System Integration Contract Matrix & Drift Audit

**Phase:** `BOOK4-PHASE-01`  
**Service/Component:** Full System (Django API Backend + FastAPI AI Service + Frontend App)  
**Role:** Book 4 Lead (Full-System Integration, DevOps, E2E, Security, AI Validation & Release)  
**Date:** September 24, 2026  
**Source-of-Truth Hierarchy:** PRD v2.3 > Explicit Shared Contracts > Approved Architecture > Cross-Book Agreements > Actual Repository Implementation > Component Prompt Books  

---

## 1. Executive Summary

This document establishes the reconciled **Integration Contract Matrix** across the three core ClarifAI subsystems:
1. **Frontend App** (React + TypeScript + Vite)
2. **Django REST API Backend** (Django + Celery + PostgreSQL)
3. **FastAPI AI Microservice** (FastAPI + PyTorch/Transformers + Qdrant)

It catalogues every internal and external endpoint, reconciles route paths across service boundaries, verifies cross-cutting security and error handling conventions, and registers all identified **Contract Drifts** for resolution in `BOOK4-PHASE-05`.

---

## 2. Django AI Client vs. FastAPI Microservice Reconciliation Matrix

The Django backend communicates with the internal FastAPI AI service via `services.ai_client.client.RealAIClient`. Below is the catalog of calls made by `RealAIClient` compared against the actual route paths exposed by FastAPI routers under `backend/fastapi-ai/app/routers/`:

| Call Site in `client.py` | Django Target Path | Actual FastAPI Exposed Route | Status | Notes / Discrepancy |
| :--- | :--- | :--- | :--- | :--- |
| `process_document()` | `POST /api/v1/process-document` | *None* (Requires multi-step pipeline invocation) | **DRIFT (P0)** | FastAPI exposes discrete processing endpoints (`/api/v1/extract-pdf`, `/api/v1/segment-clauses`, `/api/v1/categorize-clauses`, `/api/v1/classify-document-risk`, `/api/v1/summarize-document`, `/api/v1/generate-embeddings`, `/api/v1/qdrant/index-document`) instead of a single `/process-document` route. |
| `chat()` | `POST /api/v1/chat` | `POST /api/v1/chatbot/chat` | **DRIFT (P1)** | Prefix mismatch: Django calls `/api/v1/chat`, FastAPI expects `/api/v1/chatbot/chat`. |
| `compare()` | `POST /api/v1/compare` | `POST /api/v1/comparison/compare-documents` | **DRIFT (P1)** | Path mismatch: Django calls `/api/v1/compare`, FastAPI expects `/api/v1/comparison/compare-documents`. |
| `translate()` | `POST /api/v1/translate` | `POST /api/v1/translation/translate-document` | **DRIFT (P1)** | Path mismatch: Django calls `/api/v1/translate`, FastAPI expects `/api/v1/translation/translate-document`. |
| `delete_document_embeddings()` | `DELETE /api/v1/documents/{id}/embeddings` | `DELETE /api/v1/qdrant/delete-document` | **DRIFT (P1)** | Path & method mismatch: Django calls `DELETE /api/v1/documents/{id}/embeddings`, FastAPI expects `DELETE /api/v1/qdrant/delete-document` with JSON body `{"document_id": "..."}`. |

---

## 3. FastAPI AI Microservice Complete Router Inventory

The internal FastAPI service (`backend/fastapi-ai`) exposes 16 routers. Below is the complete catalog of all exposed internal endpoints:

| Router Module | Router Prefix | HTTP Method & Path | Functionality |
| :--- | :--- | :--- | :--- |
| `health.py` | *None* | `GET /health`<br>`GET /health/live`<br>`GET /health/ready` | Liveness & readiness probes |
| `pdf.py` | `/api/v1` | `POST /api/v1/extract-pdf` | PyMuPDF / Tesseract PDF text & OCR extraction |
| `text_cleaning.py` | `/api/v1` | `POST /api/v1/clean-text` | Text normalization & whitespace cleaning |
| `clause_segmentation.py` | `/api/v1` | `POST /api/v1/segment-clauses` | Regex/heuristic legal clause segmentation |
| `clause_categorization.py` | `/api/v1` | `POST /api/v1/categorize-clauses` | Zero-shot / Legal-BERT clause categorization |
| `risk.py` | `/api/v1` | `POST /api/v1/classify-risk`<br>`POST /api/v1/classify-document-risk`<br>`POST /api/v1/validate-risk-output` | Legal-BERT risk classification & score aggregation |
| `summarization.py` | `/api/v1` | `POST /api/v1/summarize`<br>`POST /api/v1/summarize-document` | BART-base abstractive legal summarization |
| `simplification.py` | `/api/v1` | `POST /api/v1/simplify-clauses` | Plain-English legal clause simplification |
| `rule_engine.py` | `/api/v1` | `POST /api/v1/evaluate-rules` | Deterministic legal compliance rule evaluation |
| `embedding.py` | `/api/v1` | `POST /api/v1/generate-embedding`<br>`POST /api/v1/generate-embeddings` | Multilingual-E5 vector embedding generation |
| `qdrant.py` | `/api/v1/qdrant` | `POST /api/v1/qdrant/index-document`<br>`POST /api/v1/qdrant/query`<br>`DELETE /api/v1/qdrant/delete-document` | Qdrant vector database indexing & vector search |
| `rag.py` | `/api/v1/rag` | `POST /api/v1/rag/retrieve-evidence` | RAG evidence retrieval from Qdrant |
| `chatbot.py` | `/api/v1/chatbot` | `POST /api/v1/chatbot/chat`<br>`DELETE /api/v1/chatbot/session/{session_id}` | Conversational RAG with GPT-OSS-20B / Groq |
| `comparison.py` | `/api/v1/comparison` | `POST /api/v1/comparison/compare-documents` | Pairwise document alignment & comparison |
| `translation.py` | `/api/v1/translation` | `POST /api/v1/translation/translate-document` | Multilingual translation engine |
| `llm.py` | `/api/v1` | `POST /api/v1/llm-completion` | Direct LLM prompt completion wrapper |

---

## 4. Public Django REST API Route Reconciliation Matrix

The public API exposed by Django (`backend/django-api/config/urls.py` and app `urls.py` modules) was reconciled against PRD v2.3 Chapter 30 and Frontend Prompt Book §8:

| Category | HTTP Method | Public Route Path | Owning Django View | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/auth/signup` | `SignUpView` | **MATCH** | PRD 30.1 & Frontend §8.1 |
| **Auth** | `POST` | `/api/auth/login` | `LoginView` | **MATCH** | PRD 30.1 & Frontend §8.1 |
| **Auth** | `POST` | `/api/auth/refresh` | `RefreshTokenView` | **MATCH** | PRD 30.1 & Frontend §8.1 |
| **Auth** | `POST` | `/api/auth/logout` | `LogoutView` | **MATCH** | PRD 30.1 & Frontend §8.1 |
| **Documents** | `GET` | `/api/documents/` | `DocumentListCreateView` | **MATCH** | PRD 30.2 & Frontend §8.2 |
| **Documents** | `POST` | `/api/documents/` | `DocumentListCreateView` | **MATCH** | PRD 30.2 & Frontend §8.2 |
| **Documents** | `GET` | `/api/documents/{id}/` | `DocumentDetailDeleteView` | **MATCH** | PRD 30.2 & Frontend §8.2 |
| **Documents** | `DELETE` | `/api/documents/{id}/` | `DocumentDetailDeleteView` | **MATCH** | PRD 30.2 & Frontend §8.2 |
| **Documents** | `GET` | `/api/documents/{id}/summary/` | `DocumentSummaryView` | **MATCH** | PRD 30.2 & Frontend §8.2 |
| **Clauses** | `GET` | `/api/documents/{id}/clauses/` | `ClauseListView` | **MATCH** | PRD 30.3 & Frontend §8.3 |
| **Clauses** | `GET` | `/api/documents/{id}/clauses/{clause_id}/` | `ClauseDetailView` | **MATCH** | PRD 30.3 & Frontend §8.3 |
| **Chat** | `GET` / `POST` | `/api/documents/{id}/chat/sessions/` | `ChatSessionGetOrCreateView` | **MATCH** | PRD 30.4 & Frontend §8.4 |
| **Chat** | `GET` / `POST` | `/api/documents/{id}/chat/messages/` | `ChatMessageListCreateView` | **MATCH** | PRD 30.4 & Frontend §8.4 |
| **Comparison** | `GET` / `POST` | `/api/comparisons/` | `ComparisonListCreateView` | **MATCH** | PRD 30.5 & Frontend §8.5 |
| **Comparison** | `GET` | `/api/comparisons/{id}/` | `ComparisonDetailView` | **MATCH** | PRD 30.5 & Frontend §8.5 |
| **Reports** | `POST` | `/api/documents/{id}/report/` | `DocumentReportCreateView` | **MATCH** | PRD 30.6 & Frontend §8.6 |
| **Reports** | `POST` | `/api/comparisons/{id}/report/` | `ComparisonReportCreateView` | **MATCH** | PRD 30.6 & Frontend §8.6 |
| **Reports** | `GET` | `/api/reports/{id}/download/` | `ReportDownloadView` | **MATCH** | PRD 30.6 & Frontend §8.6 |
| **Dashboard** | `GET` | `/api/dashboard/summary` | `DashboardSummaryView` | **MATCH** | PRD 30.7 & Frontend §8.7 |

---

## 5. Cross-Cutting Contracts Verification

| Contract Requirement | Specification Source | Repository Implementation | Status | Verification Detail |
| :--- | :--- | :--- | :--- | :--- |
| **Error Response Envelope** | PRD Ch. 30.8 & Frontend §8.8 | `core.exceptions.custom_exception_handler` | **MATCH** | Envelope shape `{ "error": { "code": ..., "message": ... } }` enforced globally for all DRF & Django errors. |
| **Rate Limiting 429 Header** | PRD Ch. 33 & Backend Part B.5.8 | DRF `Throttled` exception handler | **MATCH** | `HTTP 429 Too Many Requests` includes `Retry-After` header automatically via DRF throttling. |
| **Ownership Privacy Protection** | PRD Ch. 26.5 & Frontend §8.2 | `Document.objects.filter(user=request.user)` | **MATCH** | Unowned resource access attempts return `HTTP 404 Not Found` rather than `403 Forbidden`, preventing resource ID enumeration. |

---

## 6. Numbered Contract Drift Register

Below is the complete, prioritized log of identified Contract Drifts to be addressed in `BOOK4-PHASE-05`:

### **DRIFT-001: Missing Document Processing Pipeline Orchestration Endpoint**
* **Owning Component:** `/backend/django-api` (`RealAIClient`) & `/backend/fastapi-ai`
* **Severity:** **P0 (Critical)**
* **Description:** `RealAIClient.process_document()` calls `POST /api/v1/process-document`, but FastAPI does not expose a single `/process-document` endpoint.
* **Root Cause:** FastAPI implements discrete pipeline stage routers (`extract-pdf`, `segment-clauses`, `categorize-clauses`, `classify-document-risk`, `summarize-document`, `generate-embeddings`, `qdrant/index-document`) rather than a monolithic orchestrator endpoint.
* **Recommended Resolution (per Hierarchy):** Update Django Celery task `process_document` or `RealAIClient` to execute the sequential pipeline calls against FastAPI's exposed router endpoints, or expose a composite `/process-document` pipeline endpoint in FastAPI.

### **DRIFT-002: Internal RAG Chat Route Path Mismatch**
* **Owning Component:** `/backend/django-api` (`RealAIClient`)
* **Severity:** **P1 (High)**
* **Description:** `RealAIClient.chat()` calls `POST /api/v1/chat`, whereas FastAPI router `chatbot.py` exposes `POST /api/v1/chatbot/chat`.
* **Root Cause:** Path prefix mismatch during initial client stubbing.
* **Recommended Resolution:** Update `RealAIClient.chat()` target path to `/api/v1/chatbot/chat`.

### **DRIFT-003: Internal Document Comparison Route Path Mismatch**
* **Owning Component:** `/backend/django-api` (`RealAIClient`)
* **Severity:** **P1 (High)**
* **Description:** `RealAIClient.compare()` calls `POST /api/v1/compare`, whereas FastAPI router `comparison.py` exposes `POST /api/v1/comparison/compare-documents`.
* **Root Cause:** Path prefix mismatch during initial client stubbing.
* **Recommended Resolution:** Update `RealAIClient.compare()` target path to `/api/v1/comparison/compare-documents`.

### **DRIFT-004: Internal Document Translation Route Path Mismatch**
* **Owning Component:** `/backend/django-api` (`RealAIClient`)
* **Severity:** **P1 (High)**
* **Description:** `RealAIClient.translate()` calls `POST /api/v1/translate`, whereas FastAPI router `translation.py` exposes `POST /api/v1/translation/translate-document`.
* **Root Cause:** Path prefix mismatch during initial client stubbing.
* **Recommended Resolution:** Update `RealAIClient.translate()` target path to `/api/v1/translation/translate-document`.

### **DRIFT-005: Internal Vector Embedding Deletion Signature Mismatch**
* **Owning Component:** `/backend/django-api` (`RealAIClient`)
* **Severity:** **P1 (High)**
* **Description:** `RealAIClient.delete_document_embeddings()` calls `DELETE /api/v1/documents/{id}/embeddings`, whereas FastAPI router `qdrant.py` exposes `DELETE /api/v1/qdrant/delete-document`.
* **Root Cause:** Method and endpoint URL structural mismatch.
* **Recommended Resolution:** Update `RealAIClient.delete_document_embeddings()` to invoke `DELETE /api/v1/qdrant/delete-document` with JSON body `{"document_id": document_id}`.

---

## 7. Conclusion & Action Items

1. **Public API & Cross-Cutting Policies:** Verified 100% compliant with PRD v2.3 and Frontend Prompt Book §8 (Auth, Documents, Chat, Comparison, Reports, Dashboard, Error Envelope, Rate Limiting, 404 Privacy).
2. **Internal AI Microservice Contract:** Catalogued all 16 FastAPI routers and 5 internal AI client call sites. Identified 5 internal route mismatches (`DRIFT-001` through `DRIFT-005`).
3. **Next Steps:** Proceed to **BOOK4-PHASE-02** to validate E2E Integration and prepare for contract drift resolution in **BOOK4-PHASE-05**.
