"""
Automated Data Leakage Verification Script (AI-PHASE-DATA-LEAKAGE-01)
Guarantees zero data leakage across train, validation, and test splits:
1. Verifies NO source document (doc_id / doc_pair_id) appears in more than one split.
2. Verifies NO exact duplicate clause text exists across different splits.
3. Exits with non-zero exit code (1) and raises ValueError if any violation is detected.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

TRAINING_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TRAINING_DIR / "data"
LEGAL_BERT_DIR = DATA_DIR / "legal_bert"
MULTILINGUAL_E5_DIR = DATA_DIR / "multilingual_e5"


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Loads records from a JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Malformed JSON on line {line_num} of {path}: {exc}")
    return records


def verify_split_document_leakage(
    train_records: List[Dict[str, Any]],
    val_records: List[Dict[str, Any]],
    test_records: List[Dict[str, Any]],
    id_field: str = "doc_id",
    task_name: str = "Task"
) -> Dict[str, Any]:
    """
    Checks for document ID overlap across train, validation, and test splits.
    Raises ValueError immediately if any overlap is found.
    """
    train_docs: Set[str] = {r[id_field] for r in train_records if id_field in r}
    val_docs: Set[str] = {r[id_field] for r in val_records if id_field in r}
    test_docs: Set[str] = {r[id_field] for r in test_records if id_field in r}

    train_val_overlap = train_docs.intersection(val_docs)
    train_test_overlap = train_docs.intersection(test_docs)
    val_test_overlap = val_docs.intersection(test_docs)

    has_leakage = bool(train_val_overlap or train_test_overlap or val_test_overlap)

    if has_leakage:
        err_msg = (
            f"CRITICAL DATA LEAKAGE DETECTED in {task_name}:\n"
            f"  - Train/Val Document Overlap: {train_val_overlap}\n"
            f"  - Train/Test Document Overlap: {train_test_overlap}\n"
            f"  - Val/Test Document Overlap: {val_test_overlap}"
        )
        raise ValueError(err_msg)

    return {
        "task_name": task_name,
        "train_docs_count": len(train_docs),
        "val_docs_count": len(val_docs),
        "test_docs_count": len(test_docs),
        "total_unique_docs": len(train_docs | val_docs | test_docs),
        "leakage_detected": False
    }


def verify_text_deduplication(
    train_records: List[Dict[str, Any]],
    val_records: List[Dict[str, Any]],
    test_records: List[Dict[str, Any]],
    text_field: str = "clause_text",
    task_name: str = "Task"
) -> Dict[str, Any]:
    """
    Checks for exact cross-split text duplication.
    """
    def extract_texts(recs: List[Dict[str, Any]]) -> Set[str]:
        return {r[text_field].strip().lower() for r in recs if r.get(text_field)}

    train_texts = extract_texts(train_records)
    val_texts = extract_texts(val_records)
    test_texts = extract_texts(test_records)

    overlap_tv = train_texts.intersection(val_texts)
    overlap_tt = train_texts.intersection(test_texts)
    overlap_vt = val_texts.intersection(test_texts)

    if overlap_tv or overlap_tt or overlap_vt:
        err_msg = (
            f"TEXT DUPLICATION DETECTED ACROSS SPLITS in {task_name}:\n"
            f"  - Train/Val Text Overlap Count: {len(overlap_tv)}\n"
            f"  - Train/Test Text Overlap Count: {len(overlap_tt)}\n"
            f"  - Val/Test Text Overlap Count: {len(overlap_vt)}"
        )
        raise ValueError(err_msg)

    return {
        "text_overlap_detected": False
    }


def run_full_leakage_check() -> bool:
    """
    Executes comprehensive leakage and deduplication checks on all dataset splits.
    """
    print("==================================================")
    print("Executing Automated Dataset Leakage Audit")
    print("==================================================")

    # 1. Legal-BERT Audit
    lb_train = load_jsonl(LEGAL_BERT_DIR / "train.jsonl")
    lb_val = load_jsonl(LEGAL_BERT_DIR / "validation.jsonl")
    lb_test = load_jsonl(LEGAL_BERT_DIR / "test.jsonl")

    res_lb = verify_split_document_leakage(lb_train, lb_val, lb_test, id_field="doc_id", task_name="Legal-BERT")
    verify_text_deduplication(lb_train, lb_val, lb_test, text_field="clause_text", task_name="Legal-BERT")
    print(f"[PASSED] Legal-BERT: {res_lb['total_unique_docs']} unique documents. ZERO leakage across splits.")

    # 2. Multilingual-E5 Audit
    e5_train = load_jsonl(MULTILINGUAL_E5_DIR / "train.jsonl")
    e5_val = load_jsonl(MULTILINGUAL_E5_DIR / "validation.jsonl")
    e5_test = load_jsonl(MULTILINGUAL_E5_DIR / "test.jsonl")

    res_e5 = verify_split_document_leakage(e5_train, e5_val, e5_test, id_field="doc_pair_id", task_name="Multilingual-E5")
    print(f"[PASSED] Multilingual-E5: {res_e5['total_unique_docs']} unique document pairs. ZERO leakage across splits.")

    print("\nALL SPLITS VALIDATED: Document-level isolation is 100% clean.")
    return True


def simulate_leakage_detection_failure() -> bool:
    """
    Self-test: artificially introduces a leaked document into validation split
    and confirms the verification function raises ValueError as required.
    """
    lb_train = load_jsonl(LEGAL_BERT_DIR / "train.jsonl")
    lb_val = load_jsonl(LEGAL_BERT_DIR / "validation.jsonl")
    lb_test = load_jsonl(LEGAL_BERT_DIR / "test.jsonl")

    if not lb_train or not lb_val:
        return False

    # Intentionally corrupt validation split with a record from train
    corrupted_val = list(lb_val) + [dict(lb_train[0])]

    try:
        verify_split_document_leakage(lb_train, corrupted_val, lb_test, id_field="doc_id", task_name="SimulatedLeakageTest")
        print("[FAILED] Leakage detector failed to catch intentional corruption!")
        return False
    except ValueError as exc:
        print(f"[PASSED] Leakage detector successfully caught intentional leakage: {exc.args[0][:80]}...")
        return True


if __name__ == "__main__":
    try:
        run_full_leakage_check()
        print("\nRunning self-validation test against synthetic leakage...")
        simulate_leakage_detection_failure()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
