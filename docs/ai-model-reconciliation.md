# ClarifAI AI Model Reconciliation & Internal Route Specification

**Document Version:** 1.0.0  
**Phase:** BOOK4-PHASE-05 (Internal AI Microservice Route Reconciliation & Integration Adapter)  
**Primary Source of Truth:** PRD v2.3 Chapters 15, 16, 24, 28.1, 50, 56  
**Implementation Source of Truth:** `backend/fastapi-ai/app/routers/` & `backend/django-api/services/ai_client/`

---

## 1. Executive Summary & Architectural Decisions

This document establishes the verified, 100% matched contract between the **Django Backend API** (`backend/django-api`) and the internal **FastAPI AI Microservice** (`backend/fastapi-ai`).

### 1.1 Route Reconciliation & Placeholder Resolution
All temporary placeholder comments (Classification E) in `services/ai_client/client.py` have been permanently resolved and removed. Every Django client invocation now targets the exact, real FastAPI router endpoints exposed under `/api/v1/`.

### 1.2 Pipeline Orchestration Architecture Decision
- **Architecture**: Granular Microservice Endpoints with Django Client-Side Pipeline Orchestration.
- **Rationale**: The FastAPI service exposes granular, single-responsibility endpoints corresponding to each AI pipeline stage (extraction, cleaning, segmentation, categorization, rule evaluation, risk classification, simplification, summarization, embedding, vector indexing).
- **Execution**: The Django AI adapter (`RealAIClient.process_document()`) acts as the workflow orchestrator, invoking each granular endpoint in strict sequential order:
  $$\text{PDF Extract} \longrightarrow \text{Clean Text} \longrightarrow \text{Segment Clauses} \longrightarrow \text{Categorize Clauses} \longrightarrow \text{Evaluate Rules} \longrightarrow \text{Classify Risk} \longrightarrow \text{Simplify Clauses} \longrightarrow \text{Summarize Document} \longrightarrow \text{Generate Embeddings} \longrightarrow \text{Index in Qdrant}$$
- **Reliability & Isolation**: If any individual stage encounters errors, per-clause failure isolation (PRD Ch. 16.5) and structured fallback handling are applied. All responses are strictly validated through `services/ai_client/validators.py` before persistence into PostgreSQL.

### 1.3 Security & Secret Verification Status
- **Authentication Header**: FastAPI expects `X-Internal-Service-Secret` (via `app.core.security.verify_internal_secret`).
- **Adapter Implementation**: Django's `RealAIClient` sends both `X-Internal-Service-Secret` and `X-Internal-Secret` headers using `settings.AI_SERVICE_SECRET`.
- **Status**: MATCHED and verified across all protected FastAPI endpoints.

---

## 2. Complete Django-to-FastAPI Route Mapping Table

| # | Django Caller Method | FastAPI Route Path | HTTP Method | FastAPI Router File | Request Schema | Response Schema | Status |
|---|---|---|---|---|---|---|---|
| 1 | `RealAIClient.extract_pdf` | `/api/v1/extract-pdf` | POST | `app/routers/pdf.py` | Multipart (`file`, `enable_ocr`) | `PDFExtractionResponse` | **MATCHED** |
| 2 | `RealAIClient.clean_text` | `/api/v1/clean-text` | POST | `app/routers/text_cleaning.py` | `TextCleaningRequest` | `TextCleaningResponse` | **MATCHED** |
| 3 | `RealAIClient.segment_clauses` | `/api/v1/segment-clauses` | POST | `app/routers/clause_segmentation.py` | `ClauseSegmentationRequest` | `ClauseSegmentationResponse` | **MATCHED** |
| 4 | `RealAIClient.categorize_clauses` | `/api/v1/categorize-clauses` | POST | `app/routers/clause_categorization.py` | `ClauseCategorizationRequest` | `ClauseCategorizationResponse` | **MATCHED** |
| 5 | `RealAIClient.evaluate_rules` | `/api/v1/evaluate-rules` | POST | `app/routers/rule_engine.py` | `RuleEngineRequest` | `RuleEngineResponse` | **MATCHED** |
| 6 | `RealAIClient.classify_risk` | `/api/v1/classify-risk` | POST | `app/routers/risk.py` | `ClauseRiskRequest` | `ClauseRiskResponse` | **MATCHED** |
| 7 | `RealAIClient.classify_document_risk` | `/api/v1/classify-document-risk` | POST | `app/routers/risk.py` | `DocumentRiskRequest` | `DocumentRiskResponse` | **MATCHED** |
| 8 | `RealAIClient.validate_risk_output` | `/api/v1/validate-risk-output` | POST | `app/routers/risk.py` | `OutputValidationRequest` | `OutputValidationResponse` | **MATCHED** |
| 9 | `RealAIClient.simplify_clauses` | `/api/v1/simplify-clauses` | POST | `app/routers/simplification.py` | `SimplificationRequest` | `SimplificationResponse` | **MATCHED** |
| 10 | `RealAIClient.summarize` | `/api/v1/summarize` | POST | `app/routers/summarization.py` | `SummarizationRequest` | `SummarizationResponse` | **MATCHED** |
| 11 | `RealAIClient.summarize_document` | `/api/v1/summarize-document` | POST | `app/routers/summarization.py` | `DocumentSummaryRequest` | `DocumentSummaryResponse` | **MATCHED** |
| 12 | `RealAIClient.generate_embedding` | `/api/v1/generate-embedding` | POST | `app/routers/embedding.py` | `SingleEmbeddingRequest` | `SingleEmbeddingResponse` | **MATCHED** |
| 13 | `RealAIClient.generate_embeddings` | `/api/v1/generate-embeddings` | POST | `app/routers/embedding.py` | `EmbeddingRequest` | `EmbeddingResponse` | **MATCHED** |
| 14 | `RealAIClient.index_document_qdrant` | `/api/v1/qdrant/index-document` | POST | `app/routers/qdrant.py` | `QdrantIndexRequest` | `QdrantIndexResponse` | **MATCHED** |
| 15 | `RealAIClient.query_qdrant` | `/api/v1/qdrant/query` | POST | `app/routers/qdrant.py` | `QdrantQueryRequest` | `QdrantQueryResponse` | **MATCHED** |
| 16 | `RealAIClient.delete_document_embeddings` | `/api/v1/qdrant/delete-document` | DELETE | `app/routers/qdrant.py` | `QdrantDeleteRequest` | `QdrantDeleteResponse` | **MATCHED** |
| 17 | `RealAIClient.retrieve_rag_evidence` | `/api/v1/rag/retrieve-evidence` | POST | `app/routers/rag.py` | `RAGRequest` | `RAGEvaluationResponse` | **MATCHED** |
| 18 | `RealAIClient.chat` | `/api/v1/chatbot/chat` | POST | `app/routers/chatbot.py` | `ChatbotRequest` | `ChatbotResponse` | **MATCHED** |
| 19 | `RealAIClient.clear_chat_session` | `/api/v1/chatbot/session/{session_id}` | DELETE | `app/routers/chatbot.py` | Query Params (`user_id`, `document_id`) | `{"success": true}` | **MATCHED** |
| 20 | `RealAIClient.compare` | `/api/v1/comparison/compare-documents` | POST | `app/routers/comparison.py` | `ComparisonRequest` | `ComparisonResponse` | **MATCHED** |
| 21 | `RealAIClient.translate` | `/api/v1/translation/translate-document` | POST | `app/routers/translation.py` | `TranslationRequest` | `TranslationResponse` | **MATCHED** |
| 22 | `RealAIClient.llm_completion` | `/api/v1/llm-completion` | POST | `app/routers/llm.py` | `LLMCompletionRequest` | `LLMCompletionResponse` | **MATCHED** |
| 23 | `RealAIClient.check_health` | `/health` | GET | `app/routers/health.py` | None | `HealthStatusResponse` | **MATCHED** |
| 24 | `RealAIClient.check_liveness` | `/health/live` | GET | `app/routers/health.py` | None | `{"status": "alive"}` | **MATCHED** |
| 25 | `RealAIClient.check_readiness` | `/health/ready` | GET | `app/routers/health.py` | None | `{"status": "ready"}` | **MATCHED** |

---

## 3. Granular Route & Schema Specifications

### 3.1 Document Extraction & Cleaning
- **`POST /api/v1/extract-pdf`**: Accepts multipart PDF binary. Returns extracted plaintext, page metadata, and OCR fallback status.
- **`POST /api/v1/clean-text`**: Accepts `raw_text: str`. Applies regex cleanup, de-hyphenation, page marker retention. Returns `cleaned_text: str`.

### 3.2 Clause Segmentation & Categorization
- **`POST /api/v1/segment-clauses`**: Accepts `text: str`. Employs regex boundaries and legal delimiters to split text into numbered clause blocks.
- **`POST /api/v1/categorize-clauses`**: Accepts `clauses: list[dict]`. Uses Legal-BERT / zero-shot classification to map each clause to one of the 8 canonical PRD categories (*Payment, Termination, Renewal, Confidentiality, Liability, Intellectual Property, Privacy, Dispute Resolution*).

### 3.3 Rule Engine & Risk Classification
- **`POST /api/v1/evaluate-rules`**: Evaluates 14 deterministic rules (R001–R014) against text/clauses. Emits structured risk evidence.
- **`POST /api/v1/classify-document-risk`**: Performs multi-clause Legal-BERT risk classification (*High, Moderate, Low, Safe*) with per-clause failure isolation and conflict resolution against rule findings.
- **`POST /api/v1/validate-risk-output`**: Standalone validator resolving rule findings and raw probabilities into validated severity.

### 3.4 Simplification & Summarization
- **`POST /api/v1/simplify-clauses`**: Generates plain-English clause rewrites and why-flagged explanations.
- **`POST /api/v1/summarize-document`**: Generates structured 4-field summary (*overview, key_points, risk_profile, obligations*).

### 3.5 Vector Embeddings & Qdrant Search
- **`POST /api/v1/generate-embeddings`**: Generates 768-dimensional multilingual embeddings for clause batches using `multilingual-e5-base`.
- **`POST /api/v1/qdrant/index-document`**: Stores vectors in Qdrant collection under strict tenant/document payload isolation.
- **`DELETE /api/v1/qdrant/delete-document`**: Cascades deletion of all vector points belonging to a specific `user_id` and `document_id`.

### 3.6 Chatbot, Comparison & Translation
- **`POST /api/v1/chatbot/chat`**: RAG-grounded conversational QA with source clause references and legal disclaimer.
- **`POST /api/v1/comparison/compare-documents`**: Pairwise clause comparison returning `matched`, `changed`, and `missing` clauses with similarity scores and diff explanations.
- **`POST /api/v1/translation/translate-document`**: Translates document analysis into Hindi while preserving original text integrity.

---

## 4. Verification & Validation Summary

- **Total FastAPI Routes Checked**: 25 endpoints across 16 routers.
- **Total Django Caller Methods Implemented**: 25 matching methods in `RealAIClient`.
- **Placeholder Routes Remaining**: 0 (all Classification E items resolved).
- **Match Rate**: 100% MATCHED.
