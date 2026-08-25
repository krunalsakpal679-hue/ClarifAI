# ClarifAI AI Output Schemas Specification Document (`AI-PHASE-STRUCTURED-OUTPUT-VALIDATION`)

Per ClarifAI PRD v2.3 Chapter 56.26, this specification documents the versioned Pydantic output schemas for all **six AI pipeline output types** within ClarifAI's AI service (`/backend/fastapi-ai`).

---

## Output Schema Inventory

| Output Type | Pydantic Schema Class | File Location | Schema Version | Validation Behavior |
| :--- | :--- | :--- | :---: | :--- |
| **1. Risk Classification Result** | `DocumentRiskResponse` / `ClassifiedClauseItem` / `OutputValidationResponse` | `app/models/risk.py` | `1.0.0` | Strict enum & schema validation |
| **2. Clause Categorization Result** | `ClauseCategorizationResponse` / `CategorizedClauseItem` | `app/models/clause_categorization.py` | `1.0.0` | Strict 8-category enum validation |
| **3. Clause Simplification Result** | `SimplificationResponse` / `SimplificationResult` | `app/models/simplification.py` | `1.0.0` | Strict rewrite & why-flagged validation |
| **4. Document Summary Result** | `DocumentSummaryResponse` | `app/models/summarization.py` | `1.0.0` | 4-field executive summary validation |
| **5. Chatbot Answer Result** | `ChatbotResponse` | `app/models/chatbot.py` | `1.0.0` | Grounded answer & disclaimer validation |
| **6. Contract Comparison Result** | `ComparisonResponse` / `ClauseComparisonItem` | `app/models/comparison.py` | `1.0.0` | Match/Changed/Missing classification validation |

---

## Detailed Schema Definitions

### 1. Risk Classification Result Schema
- **Class**: `DocumentRiskResponse` / `ClassifiedClauseItem`
- **Location**: `app/models/risk.py`
- **Required Fields**: `success` (bool), `total_clauses` (int), `clauses` (list of `ClassifiedClauseItem`), `schema_version` (str).
- **Severity Enum Values**: `Safe`, `Caution`, `High`, `Moderate`.
- **Rejection Policy**: Invalid data types or missing fields trigger `ValidationError`. Safe fallback preserves verbatim clause text without defaulting to "Safe" on error.

### 2. Clause Categorization Result Schema
- **Class**: `ClauseCategorizationResponse` / `CategorizedClauseItem`
- **Location**: `app/models/clause_categorization.py`
- **Required Fields**: `position` (int), `text` (str), `character_count` (int), `categories` (list of `ClauseCategoryEnum`).
- **Allowed Categories Enum**: `Payment`, `Termination`, `Renewal`, `Confidentiality`, `Liability`, `Intellectual Property`, `Privacy`, `Dispute Resolution`.
- **Rejection Policy**: Values outside the PRD-approved 8-category set raise `ValidationError`.

### 3. Clause Simplification Result Schema
- **Class**: `SimplificationResponse` / `SimplificationResult`
- **Location**: `app/models/simplification.py`
- **Required Fields**: `position` (int), `original_text` (str), `simplified_text` (str), `severity` (str), `status` (str).
- **Rejection Policy**: Missing `simplified_text` or malformed LLM response triggers `validate_untrusted_llm_output` fallback (`simplified_text = original_text`, `status = FAILED_SIMPLIFICATION`).

### 4. Document Summary Result Schema
- **Class**: `DocumentSummaryResponse`
- **Location**: `app/models/summarization.py`
- **Required Fields**: `success` (bool), `summary_status` (str), `model_name` (str), `schema_version` (str).
- **Executive Fields**: `purpose_text`, `obligations_text`, `key_terms_text`, `key_risks_text`.
- **Rejection Policy**: Missing required fields or failed generation sets `summary_status = UNAVAILABLE` with structured `summary_error`.

### 5. Chatbot Answer Result Schema
- **Class**: `ChatbotResponse`
- **Location**: `app/models/chatbot.py`
- **Required Fields**: `answer` (str), `has_sufficient_evidence` (bool), `source_clause_ids` (list), `disclaimer` (str), `session_id` (str), `user_id` (str), `document_id` (str), `question` (str), `target_language` (str), `schema_version` (str).
- **Rejection Policy**: Invalid types or missing session/user/document IDs raise `ValidationError`. If evidence gating fails, direct `CONTROLLED_NO_ANSWER_RESPONSE` is returned without LLM call.

### 6. Contract Comparison Result Schema
- **Class**: `ComparisonResponse` / `ClauseComparisonItem`
- **Location**: `app/models/comparison.py`
- **Required Fields**: `success` (bool), `user_id` (str), `document_id_a` (str), `document_id_b` (str), `total_clauses_a` (int), `total_clauses_b` (int), `matched_count` (int), `changed_count` (int), `missing_count` (int), `comparison_results` (list of `ClauseComparisonItem`).
- **Classification Enum**: `MATCHED`, `CHANGED`, `MISSING`.
- **Rejection Policy**: Missing document IDs or invalid scores trigger `ValidationError`.

---

## Adversarial Validation Suite Summary

All 6 output schemas are covered by adversarial test cases in [`tests/test_structured_output_validation.py`](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/tests/test_structured_output_validation.py):
- **Malformed JSON**: Rejected (JSONDecodeError / ValidationError)
- **Missing Required Field**: Rejected (ValidationError)
- **Invalid Enum Value**: Rejected (ValidationError)
- **Wrong Data Type**: Rejected (ValidationError)
- **Pass Rate**: 100% (18/18 PASSED)
