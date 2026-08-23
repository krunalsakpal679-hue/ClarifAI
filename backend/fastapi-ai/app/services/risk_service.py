"""
ClarifAI Legal-BERT Clause Risk Classification Service Module
Stage 2 of the two-stage hybrid risk analysis pipeline (PRD Chapter 16.9).
Receives clause text and deterministic rule findings, then classifies severity.
Approved Severities: High, Moderate, Low, Safe (Strict 4-level model).

NOTE: Uses base 'nlpaueb/legal-bert-base-uncased' as an interim placeholder.
The fine-tuned checkpoint source/URL is IMPLEMENTATION DECISION REQUIRED.
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
        rule_findings: Optional rule findings from Stage 1 rule engine.
        
    Returns:
        Dict containing severity ('High', 'Moderate', 'Low', 'Safe'), confidence,
        logits shape, and inference latency in ms.
    """
    if not clause_text or not clause_text.strip():
        raise ValueError("Clause text for risk classification must not be empty.")

    t0 = time.time()
    try:
        tokenizer, model = load_legal_bert_model()

        # Append rule findings context to input if present (PRD Section 16.9 integration)
        input_text = clause_text.strip()
        if rule_findings:
            signals_summary = ", ".join([f.get("rule_id", "") for f in rule_findings if "rule_id" in f])
            if signals_summary:
                input_text = f"Context Signals: [{signals_summary}] Clause: {input_text}"

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
        # Strictly NEVER default to 'Safe'. Raise RuntimeError for pipeline error handler.
        raise RuntimeError(f"AI risk classification failed: {e}") from e


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
