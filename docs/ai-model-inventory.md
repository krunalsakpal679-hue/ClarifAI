# AI Dependency Inventory & Feasibility Matrix

**Service:** `/backend/fastapi-ai`  
**Role:** AI Pipeline Developer (Developer 3)  
**Project:** ClarifAI  
**Source Specification:** ClarifAI PRD v2.3 (Chapters 14, 15, 16, 19, 28.1, 29.9, 50)  
**Date:** August 23, 2026  
**Status:** Baseline Inventory Complete  

---

## 1. Executive Summary

This document establishes the official AI dependency inventory for the `/backend/fastapi-ai` microservice in the ClarifAI platform, per ClarifAI PRD v2.3 Chapter 28.1. It catalogs all 10 approved AI models, processing libraries, execution frameworks, and storage engines. Each component is defined by its operational purpose, provider source, execution tier (local process vs. cloud API), credential requirements, resource footprint, health verification pattern, failure behavior, and current hardware feasibility status based on findings from `AI-SETUP-ENVIRONMENT-01` (`/docs/ai-environment-report.md`).

---

## 2. AI Dependency Inventory Matrix

| Component / Model | Purpose | Approved Provider / Source | Execution Location | Download Req.? | Credentials Req.? | Storage & Runtime Requirement | Required Environment Variables | Failure Behavior | Feasibility Status / Decision Flag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Legal-BERT (fine-tuned)** | Clause risk classification (High, Moderate, Low, Safe), risk type, explanation, and evidence generation. | Hugging Face (`nlpaueb/legal-bert-base-uncased` base) | Local Process (`fastapi-ai`) | Yes | No | **Storage:** ~440 MB<br>**RAM:** ~1.5 GB<br>**VRAM:** ~1.0 GB (GPU) | `LEGAL_BERT_MODEL_PATH`<br>`LEGAL_BERT_MODEL_NAME` | Invalid/failed output is rejected (never defaults to Safe). Logs error; pipeline task marked failed. | `FEASIBILITY CHECK FOR AI-FEASIBILITY-01`<br>*Implementation Decision Required: Fine-tuned checkpoint path.* |
| **BART-base** | Executive summary generation (document-level and clause-level summaries). | Hugging Face (`facebook/bart-base`) | Local Process (`fastapi-ai`) | Yes | No | **Storage:** ~500 MB<br>**RAM:** ~1.5–2.0 GB<br>**VRAM:** ~1.5 GB (GPU) | `BART_MODEL_PATH`<br>`BART_MODEL_NAME` | Logs error; marks summarization pipeline stage as failed. | `FEASIBILITY CHECK FOR AI-FEASIBILITY-01`<br>*Implementation Decision Required: Summarization prompt parameters.* |
| **Groq LLM Service (`openai/gpt-oss-20b`)** | Chatbot answer generation (RAG) and plain-language clause simplification. | Groq Cloud API (`openai/gpt-oss-20b`) | External API (Groq Cloud) | No | Yes | **Storage:** 0 MB<br>**RAM:** Negligible<br>**Network:** Low latency HTTPS | `GROQ_API_KEY`<br>`GROQ_MODEL_NAME` | Catch timeout/rate-limit/5xx. Return controlled error message ("AI service temporarily unavailable"). | **VERIFIED OPERATIONAL (RESOLVED 2026-08-23)**<br>*Note: Original model llama-3.1-8b-instant was retired by Groq (shutdown 2026-08-16). Migrated per PRD Chapter 44 to provider-recommended replacement openai/gpt-oss-20b.* |
| **Multilingual-E5 (fine-tuned)** | Clause embedding generation for Qdrant vector search, RAG retrieval, and pairwise comparison similarity. | Hugging Face (`intfloat/multilingual-e5-base` / `small`) | Local Process (`fastapi-ai`) | Yes | No | **Storage:** ~470 MB – 1.1 GB<br>**RAM:** ~1.0–2.0 GB<br>**VRAM:** ~1.0 GB (GPU) | `EMBEDDING_MODEL_NAME`<br>`EMBEDDING_MODEL_PATH` | Logs embedding error; aborts vector indexing and comparison processing. | `FEASIBILITY CHECK FOR AI-FEASIBILITY-01`<br>*Implementation Decision Required: Small vs. Base variant selection.* |
| **sentence-transformers** | Python framework powering embedding generation (Multilingual-E5) and vector ops. | PyPI (`sentence-transformers`) | Local Process (`fastapi-ai`) | Yes | No | **Storage:** ~50 MB<br>**RAM:** Negligible (uses PyTorch) | None | FastAPI app fails startup if import or instantiation fails. | `VERIFIED FUNCTIONAL`<br>*Standard library requirement.* |
| **IndicTrans2** | English $\leftrightarrow$ Hindi translation for summaries, simplifications, explanations, reports, and chatbot responses. | AI4Bharat / Hugging Face (`ai4bharat/indictrans2-en-indic-1B`) | Local Process (`fastapi-ai`) | Yes | No | **Storage:** ~2.0–4.0 GB<br>**RAM:** ~4.0–8.0 GB<br>**VRAM:** ~4.0 GB (FP16) | `INDICTRANS_MODEL_PATH`<br>`TRANSLATION_ENABLED` | **Graceful Fallback:** If translation fails, English remains available and user is informed Hindi is temporarily unavailable. | `FEASIBILITY CHECK FOR AI-FEASIBILITY-01`<br>*Implementation Decision Required: Quantization (FP16/INT8/ONNX).* |
| **Tesseract OCR** | Native OCR text extraction for scanned or image-based PDF pages (adaptive per-page execution). | UB-Mannheim Tesseract distribution (v5.4.0) | Local Process (`tesseract.exe`) | Yes | No | **Storage:** ~150 MB<br>**RAM:** ~100–300 MB per page image | `TESSERACT_CMD`<br>`TESSDATA_PREFIX` | Logs extraction error; flags page as unreadable or returns partial text warning. | `FEASIBILITY CHECK FOR AI-FEASIBILITY-01`<br>*Implementation Decision Required: Missing from PATH environment variable.* |
| **PyMuPDF (`fitz`)** | Direct digital PDF text extraction, document layout parsing, and page rendering. | PyPI (`PyMuPDF` v1.23+) | Local Process (`fastapi-ai`) | Yes | No | **Storage:** ~40 MB<br>**RAM:** ~50–200 MB per PDF | None | Raises PDF parsing exception; logs corrupt file and returns failure status to Django. | `VERIFIED FUNCTIONAL`<br>*Standard C-extension wheel.* |
| **FastAPI (+ Uvicorn)** | Internal AI microservice REST API framework executing inference pipelines. | PyPI (`fastapi`, `uvicorn`) | Local Process / Container | Yes | No | **Storage:** ~20 MB<br>**RAM:** ~50–100 MB baseline | `FASTAPI_HOST`<br>`FASTAPI_PORT`<br>`INTERNAL_SERVICE_SECRET` | Service fails startup on fatal config error. Endpoints return HTTP 500/503 on unhandled errors. | `VERIFIED FUNCTIONAL`<br>*FastAPI 0.110.0 installed.* |
| **Qdrant** | Vector database storing clause embeddings for semantic search, RAG retrieval, and comparison. | Docker Image (`qdrant/qdrant`) / Qdrant Cloud | Local Container / Cloud API | Yes (if local container) | Yes (if auth enabled) | **Storage:** Persistent Volume (~100 MB–2 GB+)<br>**RAM:** ~250 MB baseline | `QDRANT_URL`<br>`QDRANT_API_KEY`<br>`QDRANT_COLLECTION_NAME` | Logs error; chatbot and comparison endpoints report vector store unreachable error safely. | `FEASIBILITY CHECK FOR AI-FEASIBILITY-01`<br>*Implementation Decision Required: Vector metric (Cosine recommended) & Docker daemon startup.* |

---

## 3. Detailed Component Specifications

### 3.1 Legal-BERT (Fine-Tuned)
* **Purpose:** Serves as stage 2 of the hybrid clause risk classification architecture (PRD Chapter 16.9). Receives clause text along with findings from the deterministic risk-signal rule engine and classifies severity (High, Moderate, Low, Safe), risk category, why-flagged explanation, and supporting evidence.
* **Approved Source / Provider:** Hugging Face Model Hub (Base: `nlpaueb/legal-bert-base-uncased`).
* **Execution Location:** Local process within `/backend/fastapi-ai`.
* **Model Loading Mechanism:** Loaded at FastAPI application startup using `AutoModelForSequenceClassification.from_pretrained()` and cached in memory.
* **Health Verification Method:** Execute a dry-run sequence classification on startup with dummy clause text to verify tensor shape and inference execution.
* **Test Verification Method:** Unit test verifying prediction output format against predefined test clauses.
* **Failure Behavior:** If Legal-BERT classification fails or returns invalid schema output, the system rejects the result (never defaulting to Safe). The error is logged and reported to Django API.
* **License Note:** Base model licensed under Apache 2.0.
* **Implementation Decision Required:** PRD v2.3 mandates a fine-tuned Legal-BERT model, but the exact Hugging Face fine-tuned checkpoint repository path / URL is unassigned.

### 3.2 BART-Base
* **Purpose:** Generates executive document-level summaries and clause-level summary highlights (PRD Chapter 28.1).
* **Approved Source / Provider:** Hugging Face Model Hub (`facebook/bart-base`).
* **Execution Location:** Local process within `/backend/fastapi-ai`.
* **Model Loading Mechanism:** Loaded at startup via `AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-base")`.
* **Health Verification Method:** Run dummy generation test (`model.generate()`) on a sample sentence during app initialization.
* **Test Verification Method:** Pytest suite testing summary text generation and length constraints.
* **Failure Behavior:** Logs summarization exception and marks the document summarization stage as failed in Celery/Django state.
* **License Note:** MIT License.
* **Implementation Decision Required:** Max length, min length, and beam search parameter defaults for summarization are not specified in PRD v2.3.

### 3.3 Llama 3.1 8B via Groq
* **Purpose:** Offloaded cloud LLM inference engine powering chatbot RAG answer generation (PRD Chapter 28.4) and plain-language clause simplification. Answers are strictly constrained to retrieved Qdrant context.
* **Approved Source / Provider:** Groq Cloud API (`llama-3.1-8b-instant`).
* **Execution Location:** External API (Groq Cloud Infrastructure).
* **Model Loading Mechanism:** Instantiated via `groq.Groq(api_key=os.getenv("GROQ_API_KEY"))` SDK client.
* **Health Verification Method:** Perform a lightweight test API call (or models list request) on startup.
* **Test Verification Method:** Unit test using mocked API responses; integration test invoking live API with test prompt.
* **Failure Behavior:** Handles API timeout, rate limits (HTTP 429), or 5xx failures gracefully by returning a controlled message ("AI service temporarily unavailable"). Never fabricates output.
* **License Note:** Subject to Groq Terms of Service & Meta Llama 3.1 Community License.
* **Environment Variables:** `GROQ_API_KEY` (holds secret key), `GROQ_MODEL_NAME`.
* **Implementation Decision Required:** Exact model ID string mapping (e.g. `llama-3.1-8b-instant` vs `llama3-8b-8192`) and exact exponential backoff retry thresholds.

### 3.4 Multilingual-E5 (Fine-Tuned)
* **Purpose:** Computes dense vector embeddings for clauses to enable vector indexing in Qdrant, semantic search for RAG chatbot context retrieval, and pairwise document comparison (PRD Chapter 28.4, 28.5).
* **Approved Source / Provider:** Hugging Face (`intfloat/multilingual-e5-base` / `intfloat/multilingual-e5-small`).
* **Execution Location:** Local process within `/backend/fastapi-ai`.
* **Model Loading Mechanism:** Loaded via `SentenceTransformer("intfloat/multilingual-e5-base")` during FastAPI lifespan initialization.
* **Health Verification Method:** Encode test string at startup and verify output vector dimensionality (e.g. 768 floats).
* **Test Verification Method:** Pytest unit test checking embedding output array shape and cosine distance calculation.
* **Failure Behavior:** If embedding fails, vector storage and comparison stages halt, returning an explicit error to Django.
* **License Note:** MIT License.
* **Implementation Decision Required:** PRD v2.3 specifies fine-tuned `Multilingual-E5`, but model size variant (`small` vs `base`) and custom fine-tuned weights repository are not specified.

### 3.5 sentence-transformers
* **Purpose:** Underlying Python framework used to instantiate, cache, and execute dense sentence vector embedding models (Multilingual-E5).
* **Approved Source / Provider:** PyPI (`sentence-transformers`).
* **Execution Location:** Local Python runtime.
* **Model Loading Mechanism:** Standard Python import (`from sentence_transformers import SentenceTransformer`).
* **Health Verification Method:** Verified during package initialization.
* **Test Verification Method:** Integrated into sentence embedding test suite.
* **Failure Behavior:** Unhandled import errors cause application startup failure.
* **License Note:** Apache 2.0.

### 3.6 IndicTrans2
* **Purpose:** Machine translation model powering English $\leftrightarrow$ Hindi translation for summaries, simplifications, explanations, reports, and chatbot output (PRD Chapter 19).
* **Approved Source / Provider:** AI4Bharat / Hugging Face (`ai4bharat/indictrans2-en-indic-1B`).
* **Execution Location:** Local process within `/backend/fastapi-ai`.
* **Model Loading Mechanism:** Loaded via Hugging Face Transformers `AutoModelForSeq2SeqLM` / `AutoTokenizer`.
* **Health Verification Method:** Run small English-to-Hindi translation sample test during application startup check.
* **Test Verification Method:** Unit test confirming translation output contains valid Hindi Unicode characters.
* **Failure Behavior:** **Graceful Fallback per PRD Chapter 19:** If translation fails, English output remains accessible, and the user is notified that Hindi is temporarily unavailable. Document analysis is NOT blocked.
* **License Note:** MIT / AI4Bharat License.
* **Implementation Decision Required:** Model quantization precision (FP16 vs INT8 vs ONNX runtime) and exact Hugging Face checkpoint weights repository path are not specified in PRD v2.3.

### 3.7 Tesseract OCR
* **Purpose:** Native C++ OCR engine for adaptive per-page text extraction from scanned or image-based PDF pages when direct PyMuPDF text extraction is insufficient (PRD Chapter 14, 15, 28.1).
* **Approved Source / Provider:** UB-Mannheim Tesseract OCR binary distribution (`v5.4.0.20240606`).
* **Execution Location:** Native binary process (`tesseract.exe`) invoked via Python `pytesseract`.
* **Model Loading Mechanism:** System subprocess execution controlled by `pytesseract`.
* **Health Verification Method:** Execute `pytesseract.get_tesseract_version()` or `tesseract --version` via subprocess on startup.
* **Test Verification Method:** Unit test running OCR on a sample image containing printed text.
* **Failure Behavior:** Logs OCR failure for target page; returns extraction warning or partial document text if unreadable.
* **Environment Variables:** `TESSERACT_CMD` (`C:\Program Files\Tesseract-OCR\tesseract.exe`), `TESSDATA_PREFIX`.
* **Implementation Decision Required:** `AI-SETUP-ENVIRONMENT-01` confirmed Tesseract is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` but is currently missing from Windows system `PATH`. Explicit `TESSERACT_CMD` environment variable or PATH registration is required.

### 3.8 PyMuPDF (`fitz`)
* **Purpose:** Extracts digital text, reads PDF structure and page dimensions, and renders page images for Tesseract OCR processing (PRD Chapter 28.1).
* **Approved Source / Provider:** PyPI (`PyMuPDF` v1.23+).
* **Execution Location:** Local process within `/backend/fastapi-ai`.
* **Model Loading Mechanism:** Python import (`import fitz`).
* **Health Verification Method:** Check `fitz.__version__` during startup inspection.
* **Test Verification Method:** Unit test opening a sample PDF file buffer and verifying page count and text extraction.
* **Failure Behavior:** Raises PyMuPDF exception on corrupted files; logs error and returns document extraction failure state.
* **License Note:** AGPL-3.0 / Commercial (Open-source compliance required).

### 3.9 FastAPI (+ Uvicorn)
* **Purpose:** Web framework hosting the internal AI microservice endpoints for document extraction, clause risk classification, summarization, chatbot RAG, comparison, and translation (PRD Chapter 28.1).
* **Approved Source / Provider:** PyPI (`fastapi`, `uvicorn`).
* **Execution Location:** Local process or container (`/backend/fastapi-ai`, default port 8000).
* **Model Loading Mechanism:** Uvicorn ASGI server loading `app.main:app` with lifespan model initialization context.
* **Health Verification Method:** Endpoint `GET /health` returning status JSON object.
* **Test Verification Method:** Pytest suite using `httpx.AsyncClient` against API routes.
* **Failure Behavior:** Critical initialization error stops server launch; unhandled endpoint exceptions return standard HTTP 500 error responses.
* **Environment Variables:** `FASTAPI_HOST`, `FASTAPI_PORT`, `INTERNAL_SERVICE_SECRET`.

### 3.10 Qdrant
* **Purpose:** Dedicated vector database storing clause-level embeddings for semantic search, chatbot RAG evidence retrieval, and pairwise document comparison (PRD Chapter 28.1, 29.9).
* **Approved Source / Provider:** Qdrant Docker Container (`qdrant/qdrant`) or Qdrant Cloud Instance.
* **Execution Location:** Local Docker container or cloud service.
* **Model Loading Mechanism:** Connection client initialized via `qdrant_client.QdrantClient(url=..., api_key=...)`.
* **Health Verification Method:** Client ping `qdrant_client.get_collections()` on app startup.
* **Test Verification Method:** Integration test creating a temporary collection, indexing sample vectors, running similarity query, and dropping collection.
* **Failure Behavior:** Unreachable Qdrant instance logs connection failure and returns controlled vector store error to Django API.
* **Environment Variables:** `QDRANT_URL`, `QDRANT_API_KEY` (secret key), `QDRANT_COLLECTION_NAME`.
* **Implementation Decision Required:** Distance metric formula (Cosine recommended) and collection payload schema parameters. Docker Desktop daemon must be running for local container execution (flagged in `AI-SETUP-ENVIRONMENT-01`).

---

## 4. Cross-Check with Hardware Feasibility (`AI-SETUP-ENVIRONMENT-01`)

The inventory findings have been cross-checked against the local environment hardware specification recorded in `/docs/ai-environment-report.md`:
* **CPU:** 13th Gen Intel Core i5-13420H (8 Cores, 12 Threads)
* **System RAM:** 16.00 GB
* **Discrete GPU:** NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM)
* **PyTorch State:** `2.10.0+cpu` (CPU-only installation detected)
* **Docker Desktop State:** CLI `29.4.2` installed; daemon currently stopped.

### Hardware Feasibility Matrix & Action Items for `AI-FEASIBILITY-01`

1. **PyTorch CUDA Upgrade (Critical):**
   * *Status:* The local environment currently has CPU-only PyTorch (`2.10.0+cpu`).
   * *Impact:* Local inference for Legal-BERT, BART-base, Multilingual-E5, and IndicTrans2 will run on CPU, resulting in higher latency and CPU resource contention.
   * *Action for `AI-FEASIBILITY-01`:* Reinstall CUDA-enabled PyTorch (`torch` compiled for CUDA 12.1/12.4) to leverage the 6 GB RTX 4050 GPU VRAM.

2. **IndicTrans2 Memory & VRAM Allocation:**
   * *Status:* IndicTrans2 (1B parameter model) requires ~4 GB VRAM in FP16 or ~4–8 GB system RAM on CPU.
   * *Impact:* Concurrent execution of Legal-BERT, BART-base, Multilingual-E5, and IndicTrans2 on a 6 GB VRAM GPU or 16 GB system RAM requires model offloading or sequential loading.
   * *Action for `AI-FEASIBILITY-01`:* Benchmark IndicTrans2 VRAM/RAM consumption and test INT8/ONNX quantization feasibility.

3. **Groq Cloud API Offloading:**
   * *Status:* Groq LLM service (`openai/gpt-oss-20b`) is hosted on Groq Cloud API.
   * *Impact:* Extremely low local hardware footprint (0 MB VRAM/RAM). Verified working with HTTP 200 responses.

4. **Tesseract Pathing:**
   * *Status:* Tesseract binary exists at `C:\Program Files\Tesseract-OCR\tesseract.exe`, but is not in Windows system `PATH`.
   * *Action for `AI-FEASIBILITY-01`:* Configure `TESSERACT_CMD` environment variable or add directory to PATH.

5. **Docker Container Stack:**
   * *Status:* Docker CLI is present, but Docker Desktop daemon is stopped.
   * *Action for `AI-FEASIBILITY-01`:* Launch Docker Desktop daemon to enable local Qdrant container testing.

---

## 5. Security & Credential Compliance

Per security directives:
1. Environment variables holding sensitive credentials:
   * `GROQ_API_KEY`: API authentication key for Groq Cloud LLM service.
   * `QDRANT_API_KEY`: Authentication key for Qdrant vector database instance.
   * `INTERNAL_SERVICE_SECRET`: Secret header token for Django $\leftrightarrow$ FastAPI internal authentication.
2. **Zero Hardcoded Credentials:** Actual credential values are never committed or documented in source control. All secrets are loaded strictly from `.env` or environment configuration.

---

## 6. Decision Register & Open Items

| Item # | Component | Description of Open Decision | Interim Safe Approach | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-AI-01** | Legal-BERT | Fine-tuned Legal-BERT checkpoint Hugging Face repository URL is not specified in PRD v2.3. | Use base `nlpaueb/legal-bert-base-uncased` with classification head stub for initial integration testing. | OPEN |
| **DEC-AI-02** | Multilingual-E5 | Exact model size (`intfloat/multilingual-e5-small` vs `base`) and fine-tuned checkpoint repo path are unspecified. | Default to `intfloat/multilingual-e5-base` (768 dimensions) for semantic embedding evaluation. | OPEN |
| **DEC-AI-03** | IndicTrans2 | Quantization format (FP16 / INT8 / ONNX) for 1B parameter model on 6 GB GPU VRAM / 16 GB RAM is unspecified. | Implement lazy model loading and evaluate INT8 / ONNX quantization during feasibility benchmarking. | OPEN |
| **DEC-AI-04** | Groq LLM | Llama 3.1 8B (`llama-3.1-8b-instant`) retired by Groq (shutdown 2026-08-16). Migrated per PRD Chapter 44. | Resolved model ID: `openai/gpt-oss-20b` (Groq provider-recommended same-platform replacement). | **RESOLVED (2026-08-23)** |
| **DEC-AI-05** | Qdrant Vector DB | Vector distance metric (Cosine / Dot / Euclidean) and collection payload schema parameters are unspecified. | Utilize Cosine similarity metric (`Distance.COSINE`) and payload schema indexed by `document_id` and `clause_id`. | OPEN |

---

## 7. Pinned Dependencies & Versioning Registry (`AI-MODEL-VERSIONING-INVENTORY-01`)

### 7.1 Pinned Python Library Dependencies (`requirements.txt`)

Every AI and microservice runtime library is strictly pinned to an exact version:

```ini
fastapi==0.129.0
uvicorn[standard]==0.41.0
pydantic==2.12.5
torch==2.10.0
transformers==5.3.0
sentence-transformers==6.0.0
pytesseract==0.3.13
PyMuPDF==1.27.1
qdrant-client==1.19.0
groq==1.6.0
httpx==0.28.1
python-dotenv==1.2.1
```

### 7.2 Active Model Checkpoints & Interim Implementation Decisions

| Component | Exact Model Checkpoint String / Path | Source / Hosting | Versioning & Implementation Notes |
| :--- | :--- | :--- | :--- |
| **Legal-BERT** | `nlpaueb/legal-bert-base-uncased` | Hugging Face Hub | **Interim Base Placeholder**: Fine-tuned checkpoint URL unassigned in PRD v2.3. Developer implementation decision to use base uncased checkpoint. |
| **BART-base** | `facebook/bart-base` | Hugging Face Hub | **Interim Base Placeholder**: Fine-tuned summarization checkpoint URL unassigned in PRD v2.3. Developer implementation decision to use base model. |
| **Multilingual-E5** | `intfloat/multilingual-e5-base` | Hugging Face Hub | **Interim Base Placeholder**: 768-dim base variant selected as developer implementation decision pending fine-tuned embedding URL. |
| **Groq LLM** | `openai/gpt-oss-20b` | Groq Cloud API | **Resolved Model**: Migrated per PRD Chapter 44 from retired `llama-3.1-8b-instant`. |
| **Tesseract OCR** | `v5.4.0.20240606` | Native OS / Image Layer | System binary `tesseract.exe` distribution with `eng+hin` language data. |

### 7.3 Schema & Prompt Versioning Registry

All microservice outputs and system prompt templates are tagged with explicit semver version strings to ensure future changes are traceable across microservice updates:

- **Global Schema Version (`SCHEMA_VERSION`):** `"1.0.0"`
- **LLM System Prompt Version (`PROMPT_VERSION`):** `"1.0.0"`
- **API Request/Response Models:** `ClauseRiskRequest`, `LLMCompletionRequest`, `SummarizationRequest` include `"schema_version": "1.0.0"`.

