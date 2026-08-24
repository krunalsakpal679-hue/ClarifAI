"""
ClarifAI BART-Base Automated Summarization Service Module
Provides executive document summarization and clause-level highlight generation
per ClarifAI PRD v2.3 Chapter 16.4, Chapter 28.1, and Chapter 50.
Includes 4-field document-level executive summarization with document-level failure isolation.

NOTE: Uses base 'facebook/bart-base' as an interim placeholder.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

# Default interim model checkpoint per PRD v2.3 Chapter 28.1
DEFAULT_SUMMARIZATION_MODEL: str = "facebook/bart-base"

# BART-base context window limit
BART_MAX_CONTEXT_TOKENS: int = 1024
CHUNK_SIZE_TOKENS: int = 800
CHUNK_OVERLAP_TOKENS: int = 100

# Schema version tag per AI-MODEL-VERSIONING-INVENTORY-01
SCHEMA_VERSION: str = "1.0.0"

_tokenizer_instance: Optional[AutoTokenizer] = None
_model_instance: Optional[AutoModelForSeq2SeqLM] = None


def get_summarization_model_name() -> str:
    """
    Retrieves SUMMARIZATION_MODEL_NAME from environment variables.
    """
    return os.getenv("SUMMARIZATION_MODEL_NAME", DEFAULT_SUMMARIZATION_MODEL)


def load_summarization_model():
    """
    Lazy loads singleton tokenizer and seq2seq model instances.
    """
    global _tokenizer_instance, _model_instance
    if _tokenizer_instance is None or _model_instance is None:
        model_name = get_summarization_model_name()
        logger.info(f"Loading BART summarization model '{model_name}'...")
        _tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
        _model_instance = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        _model_instance.eval()
    return _tokenizer_instance, _model_instance


def chunk_text_tokens(text: str, tokenizer: AutoTokenizer) -> List[str]:
    """
    Splits long document text into chunks <= CHUNK_SIZE_TOKENS with CHUNK_OVERLAP_TOKENS overlap.
    Documented strategy for handling texts exceeding the 1024 token context window.
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    if len(tokens) <= BART_MAX_CONTEXT_TOKENS:
        return [text]

    chunks = []
    start = 0
    step = CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS

    while start < len(tokens):
        end = min(start + CHUNK_SIZE_TOKENS, len(tokens))
        chunk_token_ids = tokens[start:end]
        chunk_str = tokenizer.decode(chunk_token_ids, skip_special_tokens=True)
        chunks.append(chunk_str)
        if end == len(tokens):
            break
        start += step

    return chunks


def summarize_text(
    text: str,
    max_length: int = 200,
    min_length: int = 30,
    num_beams: int = 4
) -> Dict[str, Any]:
    """
    Generates a concise executive summary for a document or clause text using BART-base.

    Args:
        text: Input document or section text.
        max_length: Maximum token length of generated summary.
        min_length: Minimum token length of generated summary.
        num_beams: Beam search size for generation decoding.

    Returns:
        Dict containing summary text, token count, latency, and chunking metadata.
    """
    if not text.strip():
        raise ValueError("Input text for summarization must not be empty.")

    t0 = time.time()
    tokenizer, model = load_summarization_model()

    chunks = chunk_text_tokens(text, tokenizer)
    is_chunked = len(chunks) > 1

    if not is_chunked:
        inputs = tokenizer(text, return_tensors="pt", max_length=BART_MAX_CONTEXT_TOKENS, truncation=True)
        with torch.no_grad():
            summary_ids = model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=num_beams,
                early_stopping=True
            )
        final_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
    else:
        # Hierarchical map-reduce summarization strategy for long documents
        chunk_summaries = []
        for c_str in chunks:
            c_inputs = tokenizer(c_str, return_tensors="pt", max_length=BART_MAX_CONTEXT_TOKENS, truncation=True)
            with torch.no_grad():
                c_ids = model.generate(
                    c_inputs["input_ids"],
                    max_length=min(120, max_length),
                    min_length=20,
                    length_penalty=1.5,
                    num_beams=2,
                    early_stopping=True
                )
            chunk_summaries.append(tokenizer.decode(c_ids[0], skip_special_tokens=True).strip())

        combined_text = " ".join(chunk_summaries)
        comb_inputs = tokenizer(combined_text, return_tensors="pt", max_length=BART_MAX_CONTEXT_TOKENS, truncation=True)
        with torch.no_grad():
            final_ids = model.generate(
                comb_inputs["input_ids"],
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=num_beams,
                early_stopping=True
            )
        final_summary = tokenizer.decode(final_ids[0], skip_special_tokens=True).strip()

    latency_ms = (time.time() - t0) * 1000
    summary_tokens = len(tokenizer.encode(final_summary, add_special_tokens=False))

    return {
        "summary": final_summary,
        "token_count": summary_tokens,
        "max_length_setting": max_length,
        "min_length_setting": min_length,
        "latency_ms": round(latency_ms, 2),
        "is_chunked": is_chunked,
        "num_chunks_processed": len(chunks),
        "model_name": get_summarization_model_name(),
        "is_interim_placeholder": True,
        "schema_version": SCHEMA_VERSION
    }


def generate_document_summary(
    clauses: List[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generates 4 structured executive document summary fields (purpose_text, obligations_text,
    key_terms_text, key_risks_text) using BART-base with document-level failure isolation (Chapter 16.4).

    Args:
        clauses: List of document clause dict items.
        rule_findings: Optional Stage 1 rule engine findings.

    Returns:
        Dict containing the 4 summary fields and summary_status ('AVAILABLE' or 'UNAVAILABLE').
    """
    model_name = get_summarization_model_name()
    if not clauses:
        logger.warning("Document summarization received empty clause list.")
        return {
            "success": True,
            "summary_status": "AVAILABLE",
            "purpose_text": "Empty document provided.",
            "obligations_text": "No obligations identified.",
            "key_terms_text": "No key terms identified.",
            "key_risks_text": "No high-severity legal risks were identified in this document.",
            "summary_error": None,
            "latency_ms": 0.0,
            "model_name": model_name,
            "schema_version": SCHEMA_VERSION
        }

    t0 = time.time()

    # Document-Level Failure Isolation (Chapter 16.4)
    try:
        # 1. Purpose Text: Summarize preamble & early clauses
        purpose_clauses = [c.get("text", "") for c in clauses[:3] if c.get("text")]
        purpose_combined = "\n".join(purpose_clauses) if purpose_clauses else "Contractual agreement between parties."
        purpose_res = summarize_text(purpose_combined, max_length=120, min_length=20)
        purpose_text = purpose_res["summary"]

        # 2. Obligations Text: Summarize obligation-heavy clauses
        obligation_clauses = [
            c.get("text", "") for c in clauses
            if any(cat in c.get("categories", []) for cat in ["Payment", "Renewal", "Termination", "Confidentiality"])
            or any(kw in c.get("text", "").lower() for kw in ["shall", "must", "agree", "obligation"])
        ]
        if not obligation_clauses:
            obligation_clauses = [c.get("text", "") for c in clauses]
        obligations_combined = "\n".join(obligation_clauses[:5])
        obligations_res = summarize_text(obligations_combined, max_length=150, min_length=30)
        obligations_text = obligations_res["summary"]

        # 3. Key Terms Text: Summarize core contractual terms
        key_term_clauses = [
            c.get("text", "") for c in clauses
            if any(cat in c.get("categories", []) for cat in ["Payment", "Dispute Resolution", "Intellectual Property", "Privacy"])
        ]
        if not key_term_clauses:
            key_term_clauses = [c.get("text", "") for c in clauses]
        key_terms_combined = "\n".join(key_term_clauses[:5])
        key_terms_res = summarize_text(key_terms_combined, max_length=150, min_length=30)
        key_terms_text = key_terms_res["summary"]

        # 4. Key Risks Text: Roll-up summary prioritizing flagged/high-severity clauses
        flagged_clauses = [
            c for c in clauses
            if c.get("severity") in ["High", "Moderate", "Low"]
            or c.get("final_severity") in ["High", "Moderate", "Low"]
            or bool(c.get("rule_findings"))
        ]

        if flagged_clauses:
            flagged_texts = [
                f"[{c.get('severity', 'Flagged')}] {c.get('text', '')}"
                for c in flagged_clauses
            ]
            risks_combined = "\n".join(flagged_texts[:6])
            risks_res = summarize_text(risks_combined, max_length=150, min_length=25)
            key_risks_text = risks_res["summary"]
        else:
            key_risks_text = "No high-severity legal risks were identified in this document."

        latency_ms = (time.time() - t0) * 1000

        logger.info(f"Document Executive Summarization Complete in {latency_ms:.2f}ms.")
        return {
            "success": True,
            "summary_status": "AVAILABLE",
            "purpose_text": purpose_text,
            "obligations_text": obligations_text,
            "key_terms_text": key_terms_text,
            "key_risks_text": key_risks_text,
            "summary_error": None,
            "latency_ms": round(latency_ms, 2),
            "model_name": model_name,
            "schema_version": SCHEMA_VERSION
        }

    except Exception as exc:
        logger.error(f"Document summary generation failed: {exc}. Surface as UNAVAILABLE without corrupting clauses.")
        return {
            "success": False,
            "summary_status": "UNAVAILABLE",
            "purpose_text": None,
            "obligations_text": None,
            "key_terms_text": None,
            "key_risks_text": None,
            "summary_error": f"Summary generation failed: {exc}",
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "model_name": model_name,
            "schema_version": SCHEMA_VERSION
        }


def get_summarization_status() -> Dict[str, Any]:
    """
    Returns diagnostic status for BART-base summarization service.
    """
    model_name = get_summarization_model_name()
    try:
        _, _ = load_summarization_model()
        return {
            "loaded": True,
            "model_name": model_name,
            "max_context_tokens": BART_MAX_CONTEXT_TOKENS,
            "chunk_size_tokens": CHUNK_SIZE_TOKENS,
            "chunk_overlap_tokens": CHUNK_OVERLAP_TOKENS,
            "is_interim_placeholder": True,
            "fine_tuned_status": "IMPLEMENTATION DECISION REQUIRED"
        }
    except Exception as e:
        logger.error(f"Summarization service status check failed: {e}")
        return {
            "loaded": False,
            "model_name": model_name,
            "error": str(e)
        }
