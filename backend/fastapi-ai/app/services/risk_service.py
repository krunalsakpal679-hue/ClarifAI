"""
ClarifAI Legal-BERT Clause Risk Classification Service Module
Stage 2 of the two-stage hybrid risk analysis pipeline (PRD Chapter 16.9).
Receives clause text and deterministic rule findings, then classifies severity.
Approved Severities: High, Moderate, Low, Safe (Strict 4-level model).
Includes per-clause failure isolation per Chapter 16.5 and Output Validation.

NOTE: Uses base 'nlpaueb/legal-bert-base-uncased' as an interim placeholder.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from app.services.output_validator_service import validate_and_resolve_clause_risk, RUNTIME_ERROR_REJECTED

logger = logging.getLogger(__name__)

# Default model checkpoint (Phase 4/5 Selected Fine-Tuned Checkpoint)
DEFAULT_LEGAL_BERT_MODEL: str = "backend/fastapi-ai/training/checkpoints/legal-bert/v2.0"

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


def resolve_legal_bert_path(model_identifier: str) -> str:
    """
    Resolves local checkpoint path or returns HuggingFace identifier.
    Supports directory aliases (legal-bert <-> legalbert).
    """
    from pathlib import Path
    variants = [model_identifier]
    if "legal-bert" in model_identifier:
        variants.append(model_identifier.replace("legal-bert", "legalbert"))
    elif "legalbert" in model_identifier:
        variants.append(model_identifier.replace("legalbert", "legal-bert"))

    for var in variants:
        candidate = Path(var)
        if candidate.exists():
            return str(candidate.resolve())

        for base in [Path(__file__).resolve().parent.parent.parent, Path.cwd()]:
            candidate_sub = base / var
            if candidate_sub.exists():
                return str(candidate_sub.resolve())
            if var.startswith("backend/fastapi-ai/"):
                rel_trimmed = var[len("backend/fastapi-ai/"):]
                candidate_trimmed = base / rel_trimmed
                if candidate_trimmed.exists():
                    return str(candidate_trimmed.resolve())
    return model_identifier


def get_legal_bert_model_name() -> str:
    """
    Returns configured Legal-BERT model name from LEGAL_BERT_MODEL_NAME env var.
    """
    return os.getenv("LEGAL_BERT_MODEL_NAME", DEFAULT_LEGAL_BERT_MODEL)


def load_legal_bert_model():
    """
    Lazy loads singleton tokenizer and classification model instances.
    Supports fine-tuned PEFT/LoRA checkpoints (v2.0) and standard HuggingFace baselines.
    """
    global _tokenizer_instance, _model_instance
    if _tokenizer_instance is None or _model_instance is None:
        from pathlib import Path
        raw_name = get_legal_bert_model_name()
        model_name = resolve_legal_bert_path(raw_name)
        logger.info(f"Loading Legal-BERT model '{raw_name}' (resolved: '{model_name}')...")

        # Check if local path contains standalone weights (merged model: config.json + safetensors/bin)
        has_direct_weights = os.path.exists(model_name) and (
            (Path(model_name) / "config.json").exists() and
            ((Path(model_name) / "model.safetensors").exists() or (Path(model_name) / "pytorch_model.bin").exists())
        )

        # Check if local path contains adapter_config.json (PEFT LoRA checkpoint)
        adapter_path = Path(model_name) / "adapter" if (Path(model_name) / "adapter" / "adapter_config.json").exists() else Path(model_name)
        is_peft = os.path.exists(model_name) and (adapter_path / "adapter_config.json").exists()

        if has_direct_weights:
            logger.info(f"Loading standalone Legal-BERT model directly from '{model_name}' without PEFT dependency...")
            _tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
            _model_instance = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(APPROVED_SEVERITY_LABELS)
            )
        elif is_peft:
            try:
                from peft import PeftModel
                from safetensors.torch import load_file

                _tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
                base_model_id = "nlpaueb/legal-bert-base-uncased"
                base_model = AutoModelForSequenceClassification.from_pretrained(
                    base_model_id,
                    num_labels=len(APPROVED_SEVERITY_LABELS)
                )
                model = PeftModel.from_pretrained(base_model, str(adapter_path))

                # Map classifier head weights if present in adapter_model.safetensors
                weights_file = adapter_path / "adapter_model.safetensors"
                if weights_file.exists():
                    weights = load_file(str(weights_file))
                    for k, v in list(weights.items()):
                        if "base_model.model.classifier.weight" in k:
                            weights["base_model.model.classifier.modules_to_save.default.weight"] = v
                            weights["base_model.model.classifier.original_module.weight"] = v
                        elif "base_model.model.classifier.bias" in k:
                            weights["base_model.model.classifier.modules_to_save.default.bias"] = v
                            weights["base_model.model.classifier.original_module.bias"] = v
                    model.load_state_dict(weights, strict=False)

                _model_instance = model
            except ImportError as peft_err:
                logger.warning(
                    f"PEFT module not installed ({peft_err}). Falling back to baseline model 'nlpaueb/legal-bert-base-uncased'..."
                )
                base_model_id = "nlpaueb/legal-bert-base-uncased"
                _tokenizer_instance = AutoTokenizer.from_pretrained(base_model_id)
                _model_instance = AutoModelForSequenceClassification.from_pretrained(
                    base_model_id,
                    num_labels=len(APPROVED_SEVERITY_LABELS)
                )
                _model_instance.eval()
                return _tokenizer_instance, _model_instance
        else:
            _tokenizer_instance = AutoTokenizer.from_pretrained(model_name)
            _model_instance = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(APPROVED_SEVERITY_LABELS)
            )

        device = os.getenv("TORCH_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        _model_instance.to(device)
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

        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

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
    Performs multi-clause risk classification with per-clause failure isolation (Chapter 16.5)
    and strict output validation / conflict resolution (Chapter 16.9, Decision R-03).

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
        raw_res: Optional[Dict[str, Any]] = None
        try:
            raw_res = classify_clause_risk(c_text, rule_findings=clause_rule_findings)
        except Exception as exc:
            logger.error(f"Per-clause risk classification failed for clause '{c_id}': {exc}.")
            raw_res = {"error": str(exc)}

        # Strict Output Validation & Conflict Resolution (Chapter 16.9, Decision R-03)
        validated_item = validate_and_resolve_clause_risk(
            clause=clause,
            raw_classification=raw_res,
            rule_findings=clause_rule_findings
        )
        # Ensure backwards compatible severity field
        validated_item["severity"] = validated_item["final_severity"] or "Safe"

        classified_items.append(validated_item)

    logger.info(f"Multi-clause Risk Classification Complete: {len(classified_items)} clauses classified & validated.")

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
        num_labels = getattr(model.config, "num_labels", len(APPROVED_SEVERITY_LABELS))
        return {
            "loaded": True,
            "model_name": model_name,
            "num_labels": num_labels,
            "approved_severities": list(APPROVED_SEVERITY_LABELS.values()),
            "is_interim_placeholder": True,
            "fine_tuned_status": "FINE-TUNED (v2.0)" if "v2.0" in model_name else "BASE"
        }
    except Exception as e:
        logger.error(f"Legal-BERT status check failed: {e}")
        return {
            "loaded": False,
            "model_name": model_name,
            "error": str(e)
        }
