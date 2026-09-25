# ClarifAI End-to-End (E2E) Test Execution Matrix

**Checkpoint Scope:** BOOK4-PHASE-15, BOOK4-PHASE-16, BOOK4-PHASE-17  
**Traceability:** PRD v2.3 Chapters 10, 14, 15, 16, 26, 30  
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

## 4. Test Suite Summary Matrix

| Component | Test Suite Path | Tests Executed | Passed | Failed | Execution Time |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Django API** | `tests/test_e2e_16_to_19_analysis_and_clauses.py` | 4 | 4 | 0 | 4.1s |
| **Django API** | `tests/test_e2e_05_to_15_document_pipeline.py` | 11 | 11 | 0 | 5.8s |
| **Django API** | `tests/test_auth.py` | 7 | 7 | 0 | 6.2s |
| **Django API** | `tests/test_documents.py` | 8 | 8 | 0 | 5.5s |
| **Django API** | `tests/test_celery_tasks.py` | 6 | 6 | 0 | 6.8s |
| **Django API** | `tests/test_real_ai_integration.py` | 5 | 5 | 0 | 4.3s |
| **FastAPI AI** | `tests/test_ocr_pipeline.py` & `test_pdf_extraction.py` | 10 | 10 | 0 | 23.8s |
| **Frontend** | `src/pages/ClauseDetail/__tests__/ClauseDetailPage.test.tsx` | 6 | 6 | 0 | 2.2s |
| **Frontend** | `src/pages/Auth/__tests__/LoginPage.test.tsx` | 13 | 13 | 0 | 1.8s |
| **Total** | | **70** | **70** | **0** | |
