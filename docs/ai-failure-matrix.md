# ClarifAI AI Pipeline Failure-Mode Matrix (`AI-PHASE-FAILURE-HANDLING`)

Per ClarifAI PRD v2.3 and Section 56.20, this document audits every failure mode across all 15 pipeline stages in ClarifAI's AI service (`/backend/fastapi-ai`).

---

## Failure-Mode Audit Matrix

| Pipeline Stage | Detection Mechanism | Response Returned | Retry Policy | User-Visible Status | Internal Logging Policy | Safe Fallback Behavior | Reprocessable |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **1. PDF Text Extraction** | PyMuPDF exception / Empty page text | HTTP 422 `UNPROCESSABLE_ENTITY` or HTTP 413 | 0 Retries (Non-transient file issue) | `"Failed to extract text from PDF"` | Log exception category & file size; NO raw document content | Triggers OCR fallback if page count $\le 5$ | Yes |
| **2. OCR Fallback** | Tesseract `TesseractNotFoundError` or zero text | HTTP 422 `UNPROCESSABLE_ENTITY` | 0 Retries | `"OCR processing failed for scanned pages"` | Log Tesseract status & error code; NO OCR text | Safe failure return; document marked unprocessable | Yes |
| **3. Clause Segmentation** | Rule-engine regex parser zero clauses | HTTP 422 `UNPROCESSABLE_ENTITY` | 0 Retries | `"Zero valid clauses detected"` | Log clause count = 0 & raw text length; NO text | Document marked unprocessable | Yes |
| **4. Legal-BERT Classification** | PyTorch model runtime exception / CUDA OOM | HTTP 500 `INTERNAL_SERVER_ERROR` | 0 Retries (Non-transient runtime) | `"AI risk classification temporarily unavailable"` | Log exception type; NO clause text or confidential data | Preserves verbatim clause text, marks status `FAILED_VALIDATION`, NEVER defaults to `Safe` | Yes |
| **5. Clause Simplification** | LLM completion failure or invalid JSON | Structured `SimplificationResponse` with `status: FAILED_SIMPLIFICATION` | 3 Retries on transient Groq errors | `"Original clause text shown"` | Log clause ID & error category; NO raw clause text | Preserves verbatim original text as `simplified_text` | Yes |
| **6. Executive Summarization** | HuggingFace BART model or LLM error | Structured `DocumentSummaryResponse` with `summary_status: UNAVAILABLE` | 3 Retries on transient LLM errors | `"Summary unavailable for this document"` | Log model name & latency; NO summary text | Returns structured error detail; document processing completes | Yes |
| **7. Clause Embedding Generation** | SentenceTransformers E5 model exception | HTTP 500 `INTERNAL_SERVER_ERROR` | 0 Retries | `"Vector embedding generation failed"` | Log model string & batch size; NO clause text | Operations requiring vector search return structured error | Yes |
| **8. Qdrant Vector Storage** | `QdrantClient` connection/API error | HTTP 503 `SERVICE_UNAVAILABLE` | 2 Retries (Transient connection) | `"Vector database service unavailable"` | Log Qdrant host & port; NO payload vector data | Returns structured vector store error; isolates user collection | Yes |
| **9. Groq LLM Calling** | `groq.APIError` or `AuthenticationError` | `RuntimeError` / HTTP 502 / 503 | 0 Retries for Auth/404; 3 for transient | `"AI processing is temporarily unavailable. Please try again later."` | Log sanitized error with API key redacted (`gsk_***[REDACTED]***`) | Safe failure isolation per clause/document | Yes |
| **10. Quota / Rate Limiting** | `groq.RateLimitError` (HTTP 429) | `RuntimeError` with `QUOTA_OR_RATE_LIMIT_EXHAUSTED` | 3 Retries with exponential backoff (2s, 4s, 8s) | `"AI processing is temporarily unavailable. Please try again later."` | Log HTTP 429 status code; NO prompt text | Exponential backoff retry; structured error on final attempt | Yes |
| **11. Timeout Handling** | `groq.APITimeoutError` / `asyncio.TimeoutError` | `RuntimeError` with `TIMEOUT` | 3 Retries | `"AI processing timed out. Please try again."` | Log configured timeout limit (30s); NO prompt text | Cancels hanging request; isolated fallback per section | Yes |
| **12. Invalid Output Rejection** | Pydantic `ValidationError` or validator check | Output safety rejection trigger | 0 Retries (Nondeterministic invalid output) | `"Structured output validation failed"` | Log schema mismatch field name; NO raw completion text | Safe verbatim text fallback for simplification/summary; controlled no-answer for chatbot | Yes |
| **13. Prompt Injection Detection** | `check_for_prompt_injection_leak` matches marker | Output safety rejection trigger | 0 Retries (Adversarial attack) | `"Prompt safety check triggered"` | Log pattern ID matched; NO document text | Immediately rejects completion; falls back to verbatim text or controlled no-answer | Yes |
| **14. Corrupted / Unsupported Input** | Unsupported mime-type / encrypted PDF | HTTP 400 or HTTP 422 | 0 Retries | `"Unsupported or corrupted document format"` | Log file extension & mime type; NO document content | Immediate request rejection | Yes |
| **15. Dependency Failure** | Network disconnect / Groq API down | HTTP 503 `SERVICE_UNAVAILABLE` | 3 Retries for transient HTTP 5xx | `"AI pipeline service dependency offline"` | Log endpoint URL host & status; NO secrets | Clean API error response; system remains stable | Yes |

---

## Failure Level Categorization

All failure payloads distinguish failure scope:
1. **Clause-Level Failures**: Per-clause status tags (`FAILED_SIMPLIFICATION`, `FAILED_VALIDATION`). Document processing continues for other clauses.
2. **Document-Level Failures**: Document status tags (`UNAVAILABLE`, `UNPROCESSABLE`). Isolated to the specific document; system remains operational.
3. **Infrastructure-Level Failures**: HTTP 503 Service Unavailable / RuntimeError. Clearly distinguished from application errors.

---

## Security & Logging Rules Enforced
- **Zero Document Content**: No raw clause or document text is written to logs during failure handling.
- **Secret Key Redaction**: All API keys match pattern `gsk_[A-Za-z0-9]+` and are sanitized as `gsk_***[REDACTED]***`.
