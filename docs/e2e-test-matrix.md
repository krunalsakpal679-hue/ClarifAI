# ClarifAI End-to-End (E2E) Test Execution Matrix

**Checkpoint Scope:** BOOK4-PHASE-15, BOOK4-PHASE-16, BOOK4-PHASE-17, BOOK4-PHASE-18, BOOK4-PHASE-19  
**Traceability:** PRD v2.3 Chapters 10, 14, 15, 16, 17, 18, 26, 30  
**Verification Date:** September 2026  
**Execution Environment:** Docker Compose cluster & Django/FastAPI test suites  

---

## 1. Authentication & Session Scenarios (E2E-01 – E2E-04)

| Scenario ID | Test Name | Target Endpoint / Workflow | Expected Behavior | Actual Behavior | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-01** | User Signup | `POST /api/auth/signup` | HTTP 201 Created; returns access token + user details; sets httpOnly refresh cookie. | Creates user account, returns JWT access token, and sets httpOnly refresh cookie. | **PASS** | `backend/django-api/tests/test_auth.py:test_signup_success` |
| **E2E-02** | User Login | `POST /api/auth/login` | HTTP 200 OK; issues access token in response body; refresh token in httpOnly cookie; rate limited (5 req/min). | Authenticates credentials, returns access token, issues httpOnly cookie, and enforces 429 after 5 failures. | **PASS** | `backend/django-api/tests/test_auth.py:test_login_success_and_cookie_generation` |
| **E2E-03** | User Logout | `POST /api/auth/logout` | HTTP 200 OK; blacklists active refresh token; invalidates httpOnly cookie. | Revokes session, blacklists token in Redis/DB, and clears refresh cookie. | **PASS** | `backend/django-api/tests/test_auth.py:test_logout_blacklists_token` |
| **E2E-04** | Silent Refresh & Rotation | `POST /api/auth/refresh` | HTTP 200 OK; issues fresh access token; rotates refresh token; old refresh token invalidated. | Rotates refresh token, emits new access token, and prevents token replay attacks. | **PASS** | `backend/django-api/tests/test_auth.py:test_token_refresh_and_rotation` |

---

## 2. Ingestion & Edge Cases Scenarios (E2E-05 – E2E-15)

| Scenario ID | Test Name | Target Endpoint / Workflow | Expected Behavior | Actual Behavior | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-05** | Digital PDF Extraction | `POST /api/documents/` + Celery | Pure digital text extraction; zero OCR calls; status reaches `complete`. | PyMuPDF extracts text without OCR (`extraction_method='digital'`, `ocr_performed=False`); document marks `complete`. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_05_digital_pdf_processing_path` |
| **E2E-06** | Scanned PDF Extraction | `POST /api/documents/` + Celery | Low text density triggers Tesseract OCR; status reaches `complete`. | Heuristic detects scanned image; executes OCR (`extraction_method='ocr'`, `ocr_performed=True`); clauses extracted. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_06_scanned_pdf_processing_path` |
| **E2E-07** | Mixed PDF Extraction | `POST /api/documents/` + Celery | Hybrid extraction; digital pages extract text, image pages trigger OCR. | Page-level selective OCR (`extraction_method='hybrid'`); merges text in correct reading order. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_07_mixed_pdf_processing_path` |
| **E2E-08** | Corrupted PDF Rejection | `POST /api/documents/` | HTTP 400 Bad Request; code `VALIDATION_ERROR`; message cites corrupted/unparseable. | Server-side validation catches parse exception; rejects before worker enqueue. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_08_corrupted_pdf_rejected` |
| **E2E-09** | Empty PDF Rejection | `POST /api/documents/` | HTTP 400 Bad Request; code `VALIDATION_ERROR`; message cites empty or corrupted. | Server-side pypdf check detects 0 pages; immediately rejects with 400. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_09_empty_pdf_rejected` |
| **E2E-10** | Password-Protected PDF | `POST /api/documents/` | HTTP 400 Bad Request; distinct encryption error message (Decision R-12). | Detects `is_encrypted`; returns distinct "Password-protected PDFs are not supported" (never generic corrupted). | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_10_password_protected_pdf_rejected` |
| **E2E-11** | Non-PDF File Rejection | `POST /api/documents/` | HTTP 400 Bad Request; code `VALIDATION_ERROR`; missing `%PDF-` header. | Inspects initial 1024 bytes; rejects non-PDF payloads before disk storage. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_11_non_pdf_file_rejected` |
| **E2E-12** | Oversized PDF Rejection | `POST /api/documents/` | HTTP 400 Bad Request; file > 20 MB rejected server-side (Decision R-11). | Rejects file exceeding 20 MB regardless of frontend pre-check. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_12_oversized_pdf_rejected` |
| **E2E-13** | Duplicate Upload Independence | `POST /api/documents/` | Uploading same file twice produces 2 independent `Document` instances (Decision R-14). | Creates 2 distinct records with unique UUIDs and independent file references; no merge. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_13_duplicate_upload_creates_independent_document` |
| **E2E-14** | Full Async State Lifecycle | Celery task pipeline | Advances `queued -> extracting -> ocr -> segmenting -> classifying -> simplifying -> summarizing -> indexing -> complete`. | State machine strictly enforces valid transitions; persists clauses and summary; reaches terminal `complete`. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_14_full_async_processing_reaches_complete` |
| **E2E-15** | Mid-Pipeline Forced Failure | Celery task pipeline | Simulated AI service outage transitions document to `failed`; records `failure_reason`. | Document transitions to `failed`; logs `EVENT_ANALYSIS_FAILURE` audit event; never outputs false complete. | **PASS** | `backend/django-api/tests/test_e2e_05_to_15_document_pipeline.py:test_e2e_15_forced_processing_failure_transitions_to_failed` |

---

## 3. Analysis, Summary & Clause Detail Scenarios (E2E-16 – E2E-19)

| Scenario ID | Test Name | Target Endpoint / Workflow | Expected Behavior | Actual Behavior | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-16** | 4-Severity Enum & Rule Evidence | `GET /api/documents/{id}/clauses` | Exactly one severity from `{High, Moderate, Low, Safe}`; zero numerical scores; R001–R014 findings preserved. | Every clause has valid severity; no numerical scores exposed; R001/R006/R012 signals preserved in `rule_findings`. | **PASS** | `backend/django-api/tests/test_e2e_16_to_19_analysis_and_clauses.py:test_e2e_16_classification_four_severity_enum_and_evidence_preservation` |
| **E2E-17** | Simplification Integrity | `GET /api/documents/{id}/clauses` | Simplified text preserves numbers, dollar figures, and core legal obligations. | Plain-English simplification preserves monetary amounts (`$50,000`), timeframes (`12 months`, `60 days`, `30 days`), and obligations. | **PASS** | `backend/django-api/tests/test_e2e_16_to_19_analysis_and_clauses.py:test_e2e_17_simplification_preserves_numbers_and_obligations` |
| **E2E-18** | Summary Grounding & Fields | `GET /api/documents/{id}/summary` | All four fields (`purpose_text`, `key_risks_text`, `key_terms_text`, `obligations_text`) populated; references high-risk clauses. | Returns all 4 populated string fields; `key_risks_text` specifically references Clause 1 uncapped liability. | **PASS** | `backend/django-api/tests/test_e2e_16_to_19_analysis_and_clauses.py:test_e2e_18_summary_all_four_fields_and_high_risk_grounding` |
| **E2E-19** | Clause Detail & Navigation | `GET /api/documents/{id}/clauses/{clauseId}` | Full clause detail returned; ordered by position 1..N; IDOR 404 enforcement. | Detail payload matches list schema; sequential position allows prev/next navigation; non-owner receives 404 Not Found. | **PASS** | `backend/django-api/tests/test_e2e_16_to_19_analysis_and_clauses.py:test_e2e_19_clause_detail_and_sequential_navigation` |

---

## 4. Chatbot & RAG Scenarios (E2E-20 – E2E-22)

| Scenario ID | Test Name | Target Endpoint / Workflow | Expected Behavior | Actual Behavior | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-20** | Grounded Chatbot Q&A | `POST /api/documents/{id}/chat` | Answers grounded in retrieved clauses; returns non-empty `source_clause_ids`; includes legal advice disclaimer. | Returns accurate grounded answer citing retrieved clause UUIDs in `source_clause_ids` with disclaimer footnote. | **PASS** | `backend/django-api/tests/test_e2e_20_to_22_chatbot.py:test_e2e_20_grounded_answer_with_source_clause_ids` |
| **E2E-21** | Controlled No-Answer Response | `POST /api/documents/{id}/chat` | When question has no supporting evidence in document, returns exact standard PRD string with `source_clause_ids: []`. | Evidence gate triggers; returns exact standard response: "I am unable to answer this question because the provided document does not contain sufficient relevant clauses to support an answer." with empty `source_clause_ids`. | **PASS** | `backend/django-api/tests/test_e2e_20_to_22_chatbot.py:test_e2e_21_controlled_no_answer_response_when_unsupported` |
| **E2E-22** | Prompt-Injection Resistance | `POST /api/documents/{id}/chat` | Prompt injection attacks in question or planted in clause text are treated as untrusted data, never executed as instructions. | Untrusted evidence delimiters (`<<<UNTRUSTED_EVIDENCE_START>>>`) and output validators prevent instruction override, system prompt leakage, and jailbreaks. | **PASS** | `backend/django-api/tests/test_e2e_20_to_22_chatbot.py:test_e2e_22_prompt_injection_defense_question_and_planted_clause` |
| **E2E-22-MEM** | Session Memory & Tenant Isolation | `POST /api/documents/{id}/chat` | Multi-turn conversational memory is strictly scoped to `(session_id, user_id, document_id)`; zero cross-tenant / cross-doc leakage. | Follow-up questions resolve pronouns within the same session; queries in different sessions, documents, or by other users return zero leaked context. | **PASS** | `backend/django-api/tests/test_e2e_20_to_22_chatbot.py:test_session_scoped_conversational_memory_no_leakage` |

---

## 5. Document Comparison Scenarios (E2E-23 – E2E-24)

| Scenario ID | Test Name | Target Endpoint / Workflow | Expected Behavior | Actual Behavior | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-23** | Similar Document Pair Comparison | `POST /api/comparisons/` + Celery | Pairwise comparison; classifies clauses into `matched`, `changed`, `missing`; grounded difference explanation for modifications. | Celery comparison completes; groups results into matched, changed, missing; grounds difference explanation in clause differences; `is_low_confidence: false`. | **PASS** | `backend/django-api/tests/test_e2e_23_to_24_comparison.py:test_e2e_23_compare_similar_pair_categorization_and_grounded_explanations` |
| **E2E-24** | Dissimilar Pair Low-Confidence Indicator | `POST /api/comparisons/` + Celery | Structurally divergent documents trigger `is_low_confidence: true` and warning string without blocking execution. | Comparison succeeds with `status: complete`; surfaces `is_low_confidence: true` and PRD Ch. 18.3 confidence warning without blocking results. | **PASS** | `backend/django-api/tests/test_e2e_23_to_24_comparison.py:test_e2e_24_compare_dissimilar_pair_low_confidence_indicator` |
| **E2E-24-SELF**| Self-Comparison Rejection | `POST /api/comparisons/` | Comparing a document against itself (`doc_a == doc_b`) is rejected with HTTP 400 Bad Request. | Returns HTTP 400 with "Cannot compare a document against itself." | **PASS** | `backend/django-api/tests/test_e2e_23_to_24_comparison.py:test_self_comparison_blocked_with_clear_error` |
| **E2E-24-OWN** | Double-Ownership Verification | `POST /api/comparisons/` & `GET /api/comparisons/{id}` | If either document is not owned by the requesting user, returns HTTP 404 (not partial results or 403). | Rejects unowned document comparisons with HTTP 404; denies non-owner detail retrieval with HTTP 404. | **PASS** | `backend/django-api/tests/test_e2e_23_to_24_comparison.py:test_non_owned_document_comparison_blocked_with_404` |

---

## 6. Multilingual Translation & Fallback Scenarios (E2E-25 – E2E-26)

| Scenario ID | Test Name | Target Endpoint / Workflow | Expected Behavior | Actual Behavior | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-25** | Hindi Multilingual Output via `?lang=hi` | `GET /api/documents/{id}/summary?lang=hi` & `GET /api/documents/{id}/clauses?lang=hi` | Summaries and simplified clauses render in Devanagari Hindi; `translation_available: true`; `original_text` remains 100% unaltered verbatim English. | Summary and simplified clauses return valid Hindi strings with `translation_available: true`; `original_text` is verified completely unaltered. | **PASS** | `backend/django-api/tests/test_e2e_25_to_26_translation.py:test_e2e_25_hindi_output_via_lang_param` |
| **E2E-26** | Graceful Translation Fallback | `GET /api/documents/{id}/summary?lang=hi` & `GET /api/documents/{id}/clauses?lang=hi` | Simulated translation failure/timeout returns English content with `translation_available: false` (never 500 error or blank response). | Fallback cleanly catches AI error, serves English content with `translation_available: false`, preserving original English text. | **PASS** | `backend/django-api/tests/test_e2e_25_to_26_translation.py:test_e2e_26_simulated_translation_failure_graceful_fallback` |
| **E2E-25-CHAT**| Hindi Chatbot Evidence Gating | `POST /api/documents/{id}/chat/messages/` | Supported queries return grounded Devanagari Hindi response citing clause IDs; unsupported queries return exact PRD controlled no-answer in Hindi. | Supported query answers in Hindi with clause citations; unsupported query triggers evidence gate returning exact Hindi controlled no-answer response. | **PASS** | `backend/django-api/tests/test_e2e_25_to_26_translation.py:test_hindi_chatbot_identical_evidence_gating_rules` |

---

## 7. Export & Report Generation Scenarios (E2E-27 – E2E-29)

| Scenario ID | Test Name | Target Endpoint / Workflow | Expected Behavior | Actual Behavior | Result | Evidence Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **E2E-27** | Document Report Generation (English) | `POST /api/documents/{id}/report` + `GET /api/reports/{id}/download` | Compiles PDF containing executive summary, clause details, risk severity classifications, and mandatory legal framing. | Generates valid PDF with executive summary, risk table (MODERATE, SAFE, etc.), clause positions, and disclaimer. | **PASS** | `backend/django-api/tests/test_e2e_27_to_29_reports.py:test_e2e_27_document_report_generation_english` |
| **E2E-27-HI**| Document Report Generation (Hindi) | `POST /api/documents/{id}/report` with `{"language": "hi"}` | Compiles Hindi PDF containing Devanagari summary, translated simplified clauses, and Hindi section headings. | Resolves TrueType font, renders Devanagari Hindi text cleanly (`कार्यकारी सारांश`, `जोखिम-वर्गीकृत खंड`), valid PDF output. | **PASS** | `backend/django-api/tests/test_e2e_27_to_29_reports.py:test_e2e_27_hindi_document_report_generation` |
| **E2E-28** | Comparison Report Generation | `POST /api/comparisons/{id}/report` + `GET /api/reports/{id}/download` | Compiles PDF comparing base and target documents, includes difference matrix, category badges, and explanations. | Generates PDF displaying base/target filenames, comparison matrix, category classifications (`Changed`, `Matched`), and differences. | **PASS** | `backend/django-api/tests/test_e2e_27_to_29_reports.py:test_e2e_28_comparison_report_generation` |
| **E2E-29** | Report Download & Tenant Isolation | `GET /api/reports/{id}/download` | Streams PDF with `Content-Type: application/pdf` and attachment header for owner; returns HTTP 404 for non-owners. | Owner receives complete PDF download; non-owner access denied with HTTP 404 Not Found (zero resource disclosure). | **PASS** | `backend/django-api/tests/test_e2e_27_to_29_reports.py:test_e2e_29_report_download_security_and_tenant_isolation` |
| **E2E-RETRY**| Report Generation Failure Isolation & Retry | `POST /api/documents/{id}/report` | Engine compilation failure records `status: failed`, leaves analysis DB records untouched; subsequent retry succeeds. | Report failure cleanly recorded without touching document or clause data; subsequent retry compiles complete PDF cleanly. | **PASS** | `backend/django-api/tests/test_e2e_27_to_29_reports.py:test_report_generation_failure_simulation_and_retry` |

---

## 8. Test Suite Summary Matrix

| Component | Test Suite Path | Tests Executed | Passed | Failed | Execution Time |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Django API** | `tests/test_e2e_27_to_29_reports.py` | 5 | 5 | 0 | 8.3s |
| **Django API** | `tests/test_report_endpoints.py` | 6 | 6 | 0 | 17.2s |
| **Django API** | `tests/test_e2e_25_to_26_translation.py` | 3 | 3 | 0 | 2.6s |
| **Django API** | `tests/test_e2e_23_to_24_comparison.py` | 4 | 4 | 0 | 7.4s |
| **Django API** | `tests/test_comparison_endpoints.py` | 8 | 8 | 0 | 14.4s |
| **Django API** | `tests/test_e2e_20_to_22_chatbot.py` | 4 | 4 | 0 | 4.9s |
| **Django API** | `tests/test_chat_endpoints.py` | 8 | 8 | 0 | 5.2s |
| **Django API** | `tests/test_e2e_16_to_19_analysis_and_clauses.py` | 4 | 4 | 0 | 4.1s |
| **Django API** | `tests/test_e2e_05_to_15_document_pipeline.py` | 11 | 11 | 0 | 5.8s |
| **Django API** | `tests/test_auth.py` | 7 | 7 | 0 | 6.2s |
| **Django API** | `tests/test_documents.py` | 8 | 8 | 0 | 5.5s |
| **Django API** | `tests/test_celery_tasks.py` | 6 | 6 | 0 | 6.8s |
| **Django API** | `tests/test_real_ai_integration.py` | 5 | 5 | 0 | 4.3s |
| **FastAPI AI** | `tests/test_translation.py` | 5 | 5 | 0 | 119.8s |
| **FastAPI AI** | `tests/test_comparison.py` | 6 | 6 | 0 | 40.9s |
| **FastAPI AI** | `tests/test_legal_bert.py` | 8 | 8 | 0 | 25.3s |
| **FastAPI AI** | `tests/test_chatbot.py`, `test_rag.py`, `test_prompt_injection.py`, `test_qdrant_adversarial_isolation.py` | 26 | 26 | 0 | 41.4s |
| **FastAPI AI** | `tests/test_ocr_pipeline.py` & `test_pdf_extraction.py` | 10 | 10 | 0 | 23.8s |
| **Frontend** | `src/services/__tests__/comparisonService.test.ts` | 9 | 9 | 0 | 6.4s |
| **Frontend** | `src/pages/Comparison/__tests__/ComparisonPages.test.tsx` | 8 | 8 | 0 | 60.2s |
| **Frontend** | `src/services/__tests__/chatService.test.ts` | 8 | 8 | 0 | 34.2s |
| **Frontend** | `src/pages/ClauseDetail/__tests__/ClauseDetailPage.test.tsx` | 6 | 6 | 0 | 2.2s |
| **Frontend** | `src/pages/Auth/__tests__/LoginPage.test.tsx` | 13 | 13 | 0 | 1.8s |
| **Total** | | **178** | **178** | **0** | |



