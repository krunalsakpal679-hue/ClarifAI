"""
Unit Tests for Training Data Integrity, Leakage Prevention, and Schema Validation (AI-PHASE-DATA-INTEGRITY-01)
"""

import pytest
import json
import sys
from pathlib import Path

BASE_FASTAPI_AI = Path(__file__).resolve().parent.parent
if str(BASE_FASTAPI_AI) not in sys.path:
    sys.path.insert(0, str(BASE_FASTAPI_AI))

from training.scripts.leakage_check import (
    load_jsonl,
    verify_split_document_leakage,
    verify_text_deduplication,
    run_full_leakage_check,
    simulate_leakage_detection_failure
)
from app.models.clause_categorization import APPROVED_CATEGORIES_SET
from app.services.risk_service import APPROVED_SEVERITY_LABELS

DATA_DIR = BASE_FASTAPI_AI / "training" / "data"
LEGAL_BERT_DIR = DATA_DIR / "legal_bert"
MULTILINGUAL_E5_DIR = DATA_DIR / "multilingual_e5"


def test_dataset_files_exist():
    """Confirms all dataset files and documentation exist on disk."""
    assert (DATA_DIR / "README.md").exists()
    assert (DATA_DIR / "DATASET_VERSION.md").exists()
    
    for split in ["train.jsonl", "validation.jsonl", "test.jsonl"]:
        assert (LEGAL_BERT_DIR / split).exists()
        assert (MULTILINGUAL_E5_DIR / split).exists()


def test_automated_leakage_check_passes():
    """Runs full automated leakage check and asserts zero violations."""
    assert run_full_leakage_check() is True


def test_leakage_detector_fails_on_intentional_violation():
    """Asserts that the leakage check script raises ValueError when leakage is introduced."""
    assert simulate_leakage_detection_failure() is True


def test_legal_bert_schema_validity():
    """Verifies that every Legal-BERT training record conforms strictly to PRD schema."""
    approved_severities = set(APPROVED_SEVERITY_LABELS.values())
    
    for split in ["train.jsonl", "validation.jsonl", "test.jsonl"]:
        records = load_jsonl(LEGAL_BERT_DIR / split)
        assert len(records) > 0
        for r in records:
            assert "doc_id" in r and r["doc_id"].strip()
            assert "clause_id" in r and r["clause_id"].strip()
            assert "clause_text" in r and r["clause_text"].strip()
            assert "context_text" in r and "[CLS]" in r["context_text"]
            assert r["severity"] in approved_severities
            assert r["category"] in APPROVED_CATEGORIES_SET
            assert r["metadata"]["origin"] == "SEED/SYNTHETIC"
            assert r["metadata"]["dataset_version"] in {"v0.1-seed", "v1.0-comprehensive"}


def test_multilingual_e5_schema_validity():
    """Verifies that every Multilingual-E5 comparison record conforms strictly to PRD schema."""
    approved_classes = {"MATCHED", "CHANGED", "MISSING"}
    
    for split in ["train.jsonl", "validation.jsonl", "test.jsonl"]:
        records = load_jsonl(MULTILINGUAL_E5_DIR / split)
        assert len(records) > 0
        for r in records:
            assert "doc_pair_id" in r and r["doc_pair_id"].strip()
            assert "doc_a_id" in r and r["doc_a_id"].strip()
            assert "doc_b_id" in r and r["doc_b_id"].strip()
            assert r["classification"] in approved_classes
            assert 0.0 <= r["target_similarity"] <= 1.0
            assert r["metadata"]["origin"] == "SEED/SYNTHETIC"
            assert r["metadata"]["dataset_version"] in {"v0.1-seed", "v1.0-comprehensive"}
            if r.get("text_a"):
                assert r["e5_text_a"].startswith("passage: ")
            if r.get("text_b"):
                assert r["e5_text_b"].startswith("passage: ")
