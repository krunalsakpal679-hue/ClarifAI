# ClarifAI AI Hallucination & Grounding Audit Document (`AI-HALLUCINATION-PREVENTION`)

Per ClarifAI PRD v2.3 Chapter 56.26, this audit documents the **Twelve Defense Layers** enforced across all five AI-generated output points within ClarifAI's AI service (`/backend/fastapi-ai`).

---

## The Five AI Generation Output Points

1. **Clause Simplification** (`app/services/simplification_service.py` $\rightarrow$ `simplified_text`)
2. **Why-Flagged Risk Explanation** (`app/services/simplification_service.py` $\rightarrow$ `why_flagged`)
3. **Document Summary** (`app/services/summarization_service.py` $\rightarrow$ `purpose`, `obligations`, `key_terms`, `key_risks`)
4. **Chatbot Conversational Answer** (`app/services/chatbot_service.py` $\rightarrow$ `answer`)
5. **Contract Comparison Difference Explanation** (`app/services/comparison_service.py` $\rightarrow$ `difference_explanation`)

---

## Twelve-Layer Hallucination Defense Audit Matrix

| Defense Layer | Simplification (`simplified_text`) | Risk Explanation (`why_flagged`) | Document Summary (`purpose`, `obligations`, `key_terms`, `key_risks`) | Chatbot Answer (`answer`) | Comparison Explanation (`difference_explanation`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Document-Only Grounding** | ✅ Active | ✅ Active | ✅ Active | ✅ Active | ✅ Active |
| **2. Vector Retrieval** | N/A (Direct Clause) | N/A (Direct Clause) | N/A (Full Doc) | ✅ Active (`user_id` + `document_id`) | ✅ Active (`user_id` + `document_id`) |
| **3. Relevance Filtering** | N/A (Direct Clause) | N/A (Direct Clause) | N/A (Full Doc) | ✅ Active ($\ge 0.65$) | ✅ Active ($\ge 0.65$) |
| **4. Sufficiency Gating** | N/A (Direct Clause) | N/A (Direct Clause) | N/A (Full Doc) | ✅ Active ($\ge 0.70$) | ✅ Active (Matched/Changed) |
| **5. Structured Prompts** | ✅ Active (`<<<UNTRUSTED>>>`) | ✅ Active (`<<<UNTRUSTED>>>`) | ✅ Active (`<<<UNTRUSTED>>>`) | ✅ Active (`<<<UNTRUSTED>>>`) | ✅ Active (`<<<UNTRUSTED>>>`) |
| **6. Explicit No-Invention** | ✅ Active | ✅ Active | ✅ Active | ✅ Active | ✅ Active |
| **7. Schema Validation** | ✅ Active (`SimplificationLLMOutput`) | ✅ Active (`SimplificationLLMOutput`) | ✅ Active (`DocumentSummary`) | ✅ Active (`ChatbotResponse`) | ✅ Active (`ComparisonResponse`) |
| **8. Unsupported-Claim Check** | ✅ Active (`check_for_hallucinated_claims`) | ✅ Active (`check_for_hallucinated_claims`) | ✅ Active (`check_for_hallucinated_claims`) | ✅ Active (`check_for_hallucinated_claims`) | ✅ Active (`check_for_hallucinated_claims`) |
| **9. Invalid-Output Rejection** | ✅ Active (`validate_untrusted_llm_output`) | ✅ Active (`validate_untrusted_llm_output`) | ✅ Active (`validate_untrusted_llm_output`) | ✅ Active (`validate_untrusted_llm_output`) | ✅ Active (`validate_untrusted_llm_output`) |
| **10. Safe Failure Isolation** | ✅ Active (Verbatim Clause Fallback) | ✅ Active ("Risk explanation unavailable") | ✅ Active (Verbatim Text Fallback) | ✅ Active (Controlled No-Answer) | ✅ Active (Similarity Summary Fallback) |
| **11. Dedicated Test Suite** | ✅ Active (`test_hallucination.py`) | ✅ Active (`test_hallucination.py`) | ✅ Active (`test_hallucination.py`) | ✅ Active (`test_hallucination.py`) | ✅ Active (`test_hallucination.py`) |
| **12. Prompt-Injection Defense** | ✅ Active (`check_for_prompt_injection_leak`) | ✅ Active (`check_for_prompt_injection_leak`) | ✅ Active (`check_for_prompt_injection_leak`) | ✅ Active (`check_for_prompt_injection_leak`) | ✅ Active (`check_for_prompt_injection_leak`) |

---

## Detailed Defense Layer Specifications

### Layer 1: Document-Only Grounding
All system prompts explicitly instruct LLMs to source content ONLY from provided clause or document text, forbidding general model knowledge presented as document facts.

### Layer 2 & 3 & 4: Retrieval, Relevance, and Sufficiency Gating
Chatbot (`chatbot_service.py`) and Comparison (`comparison_service.py`) require ownership-scoped Qdrant retrieval hard-filtered on `user_id` + `document_id`. RAG evidence retrieval requires candidate cosine similarity relevance $\ge 0.65$ and top-candidate sufficiency score $\ge 0.70$. If gating fails, direct controlled no-answer response is returned without calling the LLM.

### Layer 5: Structured Prompts
All untrusted document/clause inputs are wrapped between `<<<UNTRUSTED_EVIDENCE_START>>>` and `<<<UNTRUSTED_EVIDENCE_END>>>` using `format_untrusted_evidence_block`.

### Layer 6: Explicit No-Invention Instructions
All LLM prompts contain explicit instructions: `"DO NOT invent, infer, or hallucinate clauses, penalties, dates, dollar amounts, obligations, rights, or legal conclusions not explicitly stated in the evidence."`

### Layer 7: Schema Validation
Outputs are validated using Pydantic schemas (`SimplificationLLMOutput`, `DocumentSummary`, `ChatbotResponse`, `ComparisonResponse`).

### Layer 8 & 9 & 12: Output Validation & Hallucination/Injection Detection
Every untrusted LLM output passes through `validate_untrusted_llm_output`:
- `check_for_legal_advice`: Rejects prohibited legal counsel phrasing.
- `check_for_prompt_injection_leak`: Rejects leaked delimiters or instruction override attempts (`system prompt:`, `ignore previous instructions`, etc.).
- `check_for_hallucinated_claims`: Rejects ungrounded general-knowledge claims (`according to general legal principles`, `as per standard commercial law`, `under federal law`, etc.).

### Layer 10: Safe Failure Isolation
- **Simplification / Risk Explanation**: Falls back to verbatim clause text and safe risk message without failing the document.
- **Summary**: Falls back to verbatim text for summary fields without failing the document analysis.
- **Chatbot**: Returns controlled no-answer response (`CONTROLLED_NO_ANSWER_RESPONSE` or `HINDI_CONTROLLED_NO_ANSWER_RESPONSE`).
- **Comparison**: Falls back to similarity classification summary.

### Layer 11: Dedicated Test Suite
Covered by unit tests in [`tests/test_hallucination.py`](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/tests/test_hallucination.py) testing all 5 output points against hallucination vectors.
