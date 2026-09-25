"""
Real HTTP AI Client Implementation (PRD Phase 7).
HTTP client communicating with internal FastAPI microservice endpoints.
Fully reconciled against FastAPI routers under backend/fastapi-ai/app/routers/.
"""
import io
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Union
import requests
from django.conf import settings

from services.ai_client.exceptions import (
    AIServiceConnectionError,
    AIServiceRateLimitError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
)
from services.ai_client.validators import (
    validate_chat_response,
    validate_compare_response,
    validate_process_document_response,
    validate_translate_response,
)

logger = logging.getLogger(__name__)


class RealAIClient:
    """
    HTTP Client for calling the internal FastAPI AI microservice.
    Enforces timeout, single network-level retry, strict response validation,
    and category-specific exception mapping per PRD Ch. 56.19–56.21.
    """

    def __init__(self, base_url: str = None, secret: str = None, timeout: int = None):
        self.base_url = (base_url or getattr(settings, 'AI_SERVICE_BASE_URL', 'http://localhost:8001')).rstrip('/')
        self.secret = secret or getattr(settings, 'AI_SERVICE_SECRET', '')
        self.timeout = timeout or getattr(settings, 'AI_SERVICE_TIMEOUT', 30)

    def _get_headers(self) -> dict:
        headers = {'Content-Type': 'application/json'}
        if self.secret:
            headers['X-Internal-Secret'] = self.secret
            headers['X-Internal-Service-Secret'] = self.secret
        return headers

    def _send_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict = None,
        files: dict = None,
        params: dict = None
    ) -> dict:
        """
        Sends HTTP request to internal FastAPI microservice.
        
        Retry Policy:
        - Network Connection drops/failures: Exactly 1 single retry attempt.
        - HTTP 4xx / 5xx status codes & AI-logic errors: ZERO retries (fails immediately).
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        if files:
            # Let requests set multipart boundary automatically
            headers.pop('Content-Type', None)

        response = None
        for attempt in range(2):  # Initial attempt + 1 single retry on network drop
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=json_data,
                    files=files,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                break  # Request succeeded at HTTP transport level
            except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as net_exc:
                if attempt == 0:
                    logger.warning(f"Network error calling AI service at {url}. Retrying once: {net_exc}")
                    continue
                logger.error(f"Network connection to AI service failed after 1 retry: {net_exc}")
                raise AIServiceConnectionError(f"Network connection to AI service failed: {net_exc}") from net_exc
            except requests.exceptions.Timeout as timeout_exc:
                # Timeout is not retried to avoid compounding latency (PRD Ch. 33.12)
                logger.error(f"AI service request timed out after {self.timeout}s: {timeout_exc}")
                raise AIServiceTimeoutError(f"AI service request timed out after {self.timeout}s.") from timeout_exc
            except requests.exceptions.RequestException as req_exc:
                logger.error(f"HTTP request exception calling AI service: {req_exc}")
                raise AIServiceConnectionError(f"HTTP request error: {req_exc}") from req_exc

        if response is None:
            raise AIServiceConnectionError("No response received from AI microservice.")

        # HTTP Status Code to Exception Mapping (PRD Ch. 56.19)
        if response.status_code == 429:
            logger.error("AI microservice returned HTTP 429 Rate Limit / Free-tier quota exhaustion.")
            raise AIServiceRateLimitError("AI microservice rate limit or free-tier quota exhausted (HTTP 429).")
        elif response.status_code in (500, 502, 503, 504):
            logger.error(f"AI microservice server error (HTTP {response.status_code}).")
            raise AIServiceUnavailableError(f"AI microservice unavailable (HTTP {response.status_code}).")
        elif response.status_code >= 400:
            logger.error(f"AI microservice client error (HTTP {response.status_code}): {response.text}")
            raise AIServiceUnavailableError(f"AI microservice error (HTTP {response.status_code}): {response.text}")

        try:
            return response.json()
        except ValueError as json_exc:
            logger.error(f"Invalid JSON returned by AI microservice: {json_exc}")
            raise AIServiceUnavailableError("Invalid non-JSON response from AI microservice.") from json_exc

    # -------------------------------------------------------------------------
    # Granular AI Pipeline Stage Methods (FastAPI 1:1 Mappings)
    # -------------------------------------------------------------------------

    def extract_pdf(
        self,
        file_bytes: bytes = None,
        filename: str = "document.pdf",
        file_path: str = None,
        enable_ocr: bool = True
    ) -> dict:
        """Invokes POST /api/v1/extract-pdf on FastAPI."""
        if file_bytes is None and file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                file_bytes = f.read()

        if file_bytes is None:
            raise ValueError("Must provide either file_bytes or a valid file_path.")

        files = {"file": (filename, io.BytesIO(file_bytes), "application/pdf")}
        params = {"enable_ocr": "true" if enable_ocr else "false"}
        return self._send_request("POST", "/api/v1/extract-pdf", files=files, params=params)

    def clean_text(self, raw_text: str, preserve_page_markers: bool = True) -> dict:
        """Invokes POST /api/v1/clean-text on FastAPI."""
        payload = {
            "raw_text": raw_text,
            "preserve_page_markers": preserve_page_markers
        }
        return self._send_request("POST", "/api/v1/clean-text", json_data=payload)

    def segment_clauses(self, text: str, pages: list = None) -> dict:
        """Invokes POST /api/v1/segment-clauses on FastAPI."""
        payload = {
            "text": text,
            "pages": pages
        }
        return self._send_request("POST", "/api/v1/segment-clauses", json_data=payload)

    def categorize_clauses(self, clauses: list) -> dict:
        """Invokes POST /api/v1/categorize-clauses on FastAPI."""
        payload = {
            "clauses": clauses
        }
        return self._send_request("POST", "/api/v1/categorize-clauses", json_data=payload)

    def evaluate_rules(self, clauses: list = None, text: str = None) -> dict:
        """Invokes POST /api/v1/evaluate-rules on FastAPI."""
        payload = {
            "clauses": clauses,
            "text": text
        }
        return self._send_request("POST", "/api/v1/evaluate-rules", json_data=payload)

    def classify_risk(self, clause_text: str, rule_findings: list = None) -> dict:
        """Invokes POST /api/v1/classify-risk on FastAPI for single clause."""
        payload = {
            "clause_text": clause_text,
            "rule_findings": rule_findings or []
        }
        return self._send_request("POST", "/api/v1/classify-risk", json_data=payload)

    def classify_document_risk(self, clauses: list, rule_findings: list = None) -> dict:
        """Invokes POST /api/v1/classify-document-risk on FastAPI."""
        payload = {
            "clauses": clauses,
            "rule_findings": rule_findings or []
        }
        return self._send_request("POST", "/api/v1/classify-document-risk", json_data=payload)

    def validate_risk_output(self, clause: dict, raw_classification: dict, rule_findings: list = None) -> dict:
        """Invokes POST /api/v1/validate-risk-output on FastAPI."""
        payload = {
            "clause": clause,
            "raw_classification": raw_classification,
            "rule_findings": rule_findings or []
        }
        return self._send_request("POST", "/api/v1/validate-risk-output", json_data=payload)

    def simplify_clauses(self, clauses: list, rule_findings: list = None) -> dict:
        """Invokes POST /api/v1/simplify-clauses on FastAPI."""
        payload = {
            "clauses": clauses,
            "rule_findings": rule_findings or []
        }
        return self._send_request("POST", "/api/v1/simplify-clauses", json_data=payload)

    def summarize(self, text: str, max_length: int = 200, min_length: int = 30) -> dict:
        """Invokes POST /api/v1/summarize on FastAPI."""
        payload = {
            "text": text,
            "max_length": max_length,
            "min_length": min_length
        }
        return self._send_request("POST", "/api/v1/summarize", json_data=payload)

    def summarize_document(self, clauses: list, rule_findings: list = None) -> dict:
        """Invokes POST /api/v1/summarize-document on FastAPI."""
        payload = {
            "clauses": clauses,
            "rule_findings": rule_findings or []
        }
        return self._send_request("POST", "/api/v1/summarize-document", json_data=payload)

    def generate_embedding(self, text: str, is_query: bool = False) -> dict:
        """Invokes POST /api/v1/generate-embedding on FastAPI."""
        payload = {
            "text": text,
            "is_query": is_query
        }
        return self._send_request("POST", "/api/v1/generate-embedding", json_data=payload)

    def generate_embeddings(self, clauses: list) -> dict:
        """Invokes POST /api/v1/generate-embeddings on FastAPI."""
        payload = {
            "clauses": clauses
        }
        return self._send_request("POST", "/api/v1/generate-embeddings", json_data=payload)

    def index_document_qdrant(self, user_id: str, document_id: str, clauses: list) -> dict:
        """Invokes POST /api/v1/qdrant/index-document on FastAPI."""
        payload = {
            "user_id": str(user_id),
            "document_id": str(document_id),
            "clauses": clauses
        }
        return self._send_request("POST", "/api/v1/qdrant/index-document", json_data=payload)

    def query_qdrant(
        self,
        user_id: str,
        document_id: str,
        query_text: str = None,
        query_vector: list = None,
        top_k: int = 5
    ) -> dict:
        """Invokes POST /api/v1/qdrant/query on FastAPI."""
        payload = {
            "user_id": str(user_id),
            "document_id": str(document_id),
            "query_text": query_text,
            "query_vector": query_vector,
            "top_k": top_k
        }
        return self._send_request("POST", "/api/v1/qdrant/query", json_data=payload)

    def delete_document_embeddings(self, document_id: str, user_id: str = "default-user") -> dict:
        """
        Invokes DELETE /api/v1/qdrant/delete-document on FastAPI vector database.
        """
        payload = {
            "user_id": str(user_id or "default-user"),
            "document_id": str(document_id)
        }
        return self._send_request("DELETE", "/api/v1/qdrant/delete-document", json_data=payload)

    def retrieve_rag_evidence(
        self,
        user_id: str,
        document_id: str,
        question: str,
        top_k: int = 5,
        relevance_threshold: float = None,
        sufficiency_threshold: float = None
    ) -> dict:
        """Invokes POST /api/v1/rag/retrieve-evidence on FastAPI."""
        payload = {
            "user_id": str(user_id),
            "document_id": str(document_id),
            "question": question,
            "top_k": top_k,
            "relevance_threshold": relevance_threshold,
            "sufficiency_threshold": sufficiency_threshold
        }
        return self._send_request("POST", "/api/v1/rag/retrieve-evidence", json_data=payload)

    def llm_completion(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> dict:
        """Invokes POST /api/v1/llm-completion on FastAPI."""
        payload = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        return self._send_request("POST", "/api/v1/llm-completion", json_data=payload)

    def check_health(self) -> dict:
        """Invokes GET /health on FastAPI."""
        return self._send_request("GET", "/health")

    def check_liveness(self) -> dict:
        """Invokes GET /health/live on FastAPI."""
        return self._send_request("GET", "/health/live")

    def check_readiness(self) -> dict:
        """Invokes GET /health/ready on FastAPI."""
        return self._send_request("GET", "/health/ready")

    # -------------------------------------------------------------------------
    # Composite Feature Methods (Chatbot, Comparison, Translation)
    # -------------------------------------------------------------------------

    def chat(
        self,
        document_id: str,
        message: str,
        history: list = None,
        user_id: str = "default-user",
        session_id: str = None,
        top_k: int = 5,
        target_language: str = "en"
    ) -> dict:
        """
        Invokes POST /api/v1/chatbot/chat on internal FastAPI microservice.
        """
        payload = {
            "session_id": session_id or str(uuid.uuid4()),
            "user_id": str(user_id or "default-user"),
            "document_id": str(document_id),
            "question": str(message),
            "top_k": top_k or 5,
            "target_language": target_language or "en"
        }
        raw_response = self._send_request("POST", "/api/v1/chatbot/chat", json_data=payload)
        return validate_chat_response(raw_response)

    def clear_chat_session(
        self,
        session_id: str,
        user_id: str = "default-user",
        document_id: str = ""
    ) -> dict:
        """
        Invokes DELETE /api/v1/chatbot/session/{session_id} on FastAPI.
        """
        params = {
            "user_id": str(user_id or "default-user"),
            "document_id": str(document_id or "")
        }
        return self._send_request("DELETE", f"/api/v1/chatbot/session/{session_id}", params=params)

    def compare(
        self,
        document_a_id: str,
        document_b_id: str,
        user_id: str = "default-user",
        matched_threshold: float = 0.85,
        changed_threshold: float = 0.50
    ) -> dict:
        """
        Invokes POST /api/v1/comparison/compare-documents on internal FastAPI microservice.
        """
        payload = {
            "user_id": str(user_id or "default-user"),
            "document_id_a": str(document_a_id),
            "document_id_b": str(document_b_id),
            "matched_threshold": matched_threshold,
            "changed_threshold": changed_threshold
        }
        raw_response = self._send_request(
            "POST",
            "/api/v1/comparison/compare-documents",
            json_data=payload
        )
        return validate_compare_response(raw_response)

    def translate(
        self,
        document_id: str,
        target_lang: str = "hi",
        fields: list = None,
        summary: dict = None,
        clauses: list = None,
        user_id: str = "default-user"
    ) -> dict:
        """
        Invokes POST /api/v1/translation/translate-document on internal FastAPI microservice.
        """
        payload = {
            "user_id": str(user_id or "default-user"),
            "document_id": str(document_id),
            "summary": summary or {},
            "clauses": clauses or [],
            "target_language": str(target_lang or "hi")
        }
        raw_response = self._send_request(
            "POST",
            "/api/v1/translation/translate-document",
            json_data=payload
        )
        # Adapt response for validator if needed
        if "target_lang" not in raw_response:
            raw_response["target_lang"] = raw_response.get("target_language", target_lang)
        if "translated_content" not in raw_response:
            raw_response["translated_content"] = {
                "summary": raw_response.get("summary_hi") or raw_response.get("summary") or {},
                "clauses": raw_response.get("clauses_hi") or raw_response.get("clauses") or []
            }
        return validate_translate_response(raw_response)

    # -------------------------------------------------------------------------
    # Full Document Pipeline Orchestration
    # -------------------------------------------------------------------------

    def process_document(
        self,
        document_id: str,
        file_reference: str,
        user_id: str = "default-user",
        raw_text: str = None
    ) -> dict:
        """
        Orchestrates the complete 10-stage AI document processing pipeline across
        the granular FastAPI endpoints in strict sequential order:
        1. PDF Extraction -> 2. Text Cleaning -> 3. Clause Segmentation ->
        4. Clause Categorization -> 5. Rule Engine -> 6. Risk Classification ->
        7. Simplification -> 8. Document Summarization -> 9. Embeddings & Qdrant Indexing.
        """
        # Step 1: Extract PDF text or resolve raw text
        extracted_text = raw_text
        pages_metadata = None

        if not extracted_text:
            # Check if file_reference exists on filesystem
            resolved_path = file_reference
            if not os.path.isabs(resolved_path) and hasattr(settings, 'MEDIA_ROOT'):
                candidate = os.path.join(settings.MEDIA_ROOT, file_reference)
                if os.path.exists(candidate):
                    resolved_path = candidate

            if os.path.exists(resolved_path) and resolved_path.lower().endswith('.pdf'):
                with open(resolved_path, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                extract_res = self.extract_pdf(file_bytes=pdf_bytes, filename=os.path.basename(resolved_path))
                extracted_text = extract_res.get('full_text', '')
                pages_metadata = extract_res.get('pages', [])
            else:
                # Fallback: check if Django default_storage can open the file_reference
                try:
                    from django.core.files.storage import default_storage
                    if default_storage.exists(file_reference):
                        with default_storage.open(file_reference, 'rb') as pdf_file:
                            pdf_bytes = pdf_file.read()
                        extract_res = self.extract_pdf(file_bytes=pdf_bytes, filename=os.path.basename(file_reference))
                        extracted_text = extract_res.get('full_text', '')
                        pages_metadata = extract_res.get('pages', [])
                except Exception as storage_exc:
                    logger.debug(f"default_storage fallback check failed for {file_reference}: {storage_exc}")

                if not extracted_text:
                    # Fallback: treat file_reference itself as plain text content if not a valid file path
                    extracted_text = file_reference

        # Step 2: Clean Text
        clean_res = self.clean_text(extracted_text or "")
        cleaned_text = clean_res.get('cleaned_text', extracted_text or "")

        # Step 3: Segment Clauses
        segment_res = self.segment_clauses(cleaned_text, pages=pages_metadata)
        segmented_clauses = segment_res.get('clauses', [])

        # Step 4: Categorize Clauses
        categorize_res = self.categorize_clauses(segmented_clauses)
        categorized_clauses = categorize_res.get('categorized_clauses', segmented_clauses)

        # Step 5: Evaluate Rules
        rule_res = self.evaluate_rules(clauses=categorized_clauses, text=cleaned_text)
        rule_findings = rule_res.get('findings', [])

        # Step 6: Classify Risk
        risk_res = self.classify_document_risk(categorized_clauses, rule_findings=rule_findings)
        classified_clauses = risk_res.get('classified_clauses', categorized_clauses)

        # Step 7: Simplify Clauses
        simplify_res = self.simplify_clauses(classified_clauses, rule_findings=rule_findings)
        simplified_clauses = simplify_res.get('simplified_clauses', classified_clauses)

        # Step 8: Summarize Document
        summary_res = self.summarize_document(classified_clauses, rule_findings=rule_findings)
        summary_payload = summary_res.get('summary', {})

        # Step 9: Generate Embeddings & Index in Qdrant Vector DB
        try:
            embed_res = self.generate_embeddings(classified_clauses)
            embedded_clauses = embed_res.get('embedded_clauses', classified_clauses)
            self.index_document_qdrant(
                user_id=user_id,
                document_id=document_id,
                clauses=embedded_clauses
            )
        except Exception as qdrant_exc:
            logger.warning(f"Vector indexing non-fatal warning for doc {document_id}: {qdrant_exc}")

        # Step 10: Assemble Complete Normalized Payload
        assembled_clauses = []
        # Index simplifications by position/id
        simp_map = {
            sc.get('position', idx): sc
            for idx, sc in enumerate(simplified_clauses, start=1)
        }

        for idx, cl in enumerate(classified_clauses, start=1):
            pos = cl.get('position', idx)
            simp = simp_map.get(pos, {})
            
            raw_sev = str(cl.get('severity', 'safe')).lower()
            if raw_sev not in ('high', 'moderate', 'low', 'safe'):
                raw_sev = 'safe'

            raw_cat = cl.get('category', 'General')
            if raw_cat not in {
                'Payment', 'Termination', 'Renewal', 'Confidentiality',
                'Liability', 'Intellectual Property', 'Privacy', 'Dispute Resolution'
            }:
                raw_cat = 'Dispute Resolution'  # Canonical fallback category

            orig_text = cl.get('text') or cl.get('original_text') or f"Clause {pos}"
            simp_text = simp.get('simplified_text') or cl.get('simplified_text') or orig_text
            explanation = simp.get('why_flagged') or simp.get('explanation') or cl.get('explanation') or 'Standard clause analysis.'

            assembled_clauses.append({
                "clause_id": f"c-{pos:03d}",
                "position": pos,
                "original_text": orig_text,
                "simplified_text": simp_text,
                "explanation": explanation,
                "severity": raw_sev,
                "category": raw_cat,
                "status": "complete",
                "rule_findings": cl.get('rule_findings', [])
            })

        response_payload = {
            "document_id": str(document_id),
            "summary": summary_payload,
            "clauses": assembled_clauses
        }

        return validate_process_document_response(response_payload)
