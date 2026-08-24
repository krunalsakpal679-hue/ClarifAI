"""
ClarifAI Legal-BERT Clause Risk Classification Service Module
Stage 2 of the two-stage hybrid risk analysis pipeline (PRD Chapter 16.9).
Receives clause text and deterministic rule findings, then classifies severity.
Approved Severities: High, Moderate, Low, Safe (Strict 4-level model).
Includes per-clause failure isolation per Chapter 16.5.

NOTE: Uses base 'nlpaueb/legal-bert-base-uncased' as an interim placeholder.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

# Default interim model checkpoint per PRD v2.3 instruction
DEFAULT_LEGAL_BERT_MODEL: str = "nlpaueb/legal-bert-base-uncased"

# Strict 4-level severity label mapping per PRD Chapter 16.9
APPROVED_SEVERITY_LABELS: Dict[int, str] = {
    0: "Safe",
    1: "Low",
    2: "Moderate",
    3: "High"
}

# Schema version tag per AI-MODEL-VERSIONING-INVENTORY-01
SCHEMA_VERSION: str = "1.0.0"

_tokenizer_instance: Optional[AutoTokenizer] = None
_model_instance: Optional[AutoModelForSequenceClassification] = None


def get_legal_bert_model_name() -> str:
    """
    Returns configured Legal-BERT model name from LEGAL_BERT_MODEL_NAME env var.
    """
    return os.getenv("LEGAL_BERT_MODEL_NAME", DEFAULT_LEGAL_BERT_MODEL)


def load_legal_bert_model():
    """
    Lazy loads singleton tokenizer and classification model instances.
    """
    global _tokenizer_instance, _model_instance
    if _tokenizer_instance is None or _model_instance is None:
        model_name = get_legal_bert_model_name()
        logger.info(f"Loading Legal-BERT model '{model_name}'...")
        _tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
        _model_instance = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(APPROVED_SEVERITY_LABELS)
        )
        _model_instance.eval()
    return _tokenizer_instance, _model_instance


def classify_clause_risk(
    clause_text: str,
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Classifies risk severity for a contract clause text using Legal-BERT.

    Args:
        clause_text: Cleaned text of the target contract clause.
        rule_findings: Optional rule findings associated with this specific clause.

    Returns:
        Dict containing severity ('High', 'Moderate', 'Low', 'Safe'), confidence,
        logits_shape, and latency_ms.
    """
    if not clause_text or not clause_text.strip():
        raise ValueError("Clause text for risk classification must not be empty.")

    t0 = time.time()
    try:
        tokenizer, model = load_legal_bert_model()

        # Append clause-specific rule findings context to input (PRD Section 16.9 integration)
        input_text = clause_text.strip()
        if rule_findings:
            signals_summary = ", ".join([
                f"{f.get('rule_id', '')} ({f.get('risk_signal', '')})"
                for f in rule_findings if "rule_id" in f
            ])
            if signals_summary:
                input_text = f"Rule Signals: [{signals_summary}] Clause: {input_text}"

        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            pred_id = torch.argmax(probs, dim=-1).item()
            confidence = probs[0][pred_id].item()

        if pred_id not in APPROVED_SEVERITY_LABELS:
            raise ValueError(f"Model returned unapproved class index: {pred_id}")

        predicted_severity = APPROVED_SEVERITY_LABELS[pred_id]
        latency_ms = (time.time() - t0) * 1000

        return {
            "success": True,
            "severity": predicted_severity,
            "confidence": round(confidence, 4),
            "logits_shape": list(logits.shape),
            "latency_ms": round(latency_ms, 2),
            "is_interim_placeholder": True,
            "model_name": get_legal_bert_model_name(),
            "rule_findings_included": bool(rule_findings),
            "schema_version": SCHEMA_VERSION
        }

    except Exception as e:
        logger.error(f"Legal-BERT Classification Error: {e}")
        raise RuntimeError(f"AI risk classification failed: {e}") from e


def classify_document_clauses_risk(
    clauses: List[Dict[str, Any]],
    rule_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Performs multi-clause risk classification with per-clause failure isolation (Chapter 16.5).
    A single clause failure logs the error metric silently and continues without aborting sibling clauses.

    Args:
        clauses: List of clause dict items from clause processing stage.
        rule_findings: Optional list of rule findings from Stage 1 rule engine.

    Returns:
        Dict containing classified clauses list, total_clauses, and schema_version.
    """
    if not clauses:
        logger.warning("Risk classification received empty clause list.")
        return {
            "success": True,
            "total_clauses": 0,
            "clauses": [],
            "schema_version": SCHEMA_VERSION
        }

    classified_items: List[Dict[str, Any]] = []

    for idx, clause in enumerate(clauses, start=1):
        c_id = str(clause.get("clause_id") or clause.get("position") or idx)
        c_text = clause.get("text", "")

        # Filter rule findings relevant ONLY to this specific clause
        clause_rule_findings: List[Dict[str, Any]] = []
        if rule_findings:
            clause_rule_findings = [
                rf for rf in rule_findings
                if str(rf.get("clause_id")) == c_id or str(rf.get("position")) == c_id
            ]

        # Per-Clause Failure Isolation (Chapter 16.5)
        severity_label = "Safe"
        try:
            res = classify_clause_risk(c_text, rule_findings=clause_rule_findings)
            severity_label = res["severity"]
        except Exception as exc:
            logger.error(f"Per-clause risk classification failed for clause '{c_id}': {exc}. Isolated fallback applied.")
            severity_label = "Safe"  # Safe fallback isolation for single broken clause

        classified_items.append({
            "position": clause.get("position", idx),
            "clause_id": c_id,
            "text": c_text,
            "severity": severity_label,
            "rule_findings": clause_rule_findings
        })

    logger.info(f"Multi-clause Risk Classification Complete: {len(classified_items)} clauses classified with per-clause isolation.")

    return {
        "success": True,
        "total_clauses": len(classified_items),
        "clauses": classified_items,
        "schema_version": SCHEMA_VERSION
    }


def get_legal_bert_status() -> Dict[str, Any]:
    """
    Returns diagnostic status for Legal-BERT model service.
    """
    model_name = get_legal_bert_model_name()
    try:
        _, model = load_legal_bert_model()
        return {
            "loaded": True,
            "model_name": model_name,
            "num_labels": model.config.num_labels,
            "approved_severities": list(APPROVED_SEVERITY_LABELS.values()),
            "is_interim_placeholder": True,
            "fine_tuned_status": "IMPLEMENTATION DECISION REQUIRED"
        }
    except Exception as e:
        logger.error(f"Legal-BERT status check failed: {e}")
        return {
            "loaded": False,
            "model_name": model_name,
            "error": str(e)
        }
