"""
Class Balance and Distribution Report Generator (AI-PHASE-DATA-BALANCE-01)
Analyzes and reports exact counts, percentages, and class distributions for:
1. Legal-BERT: Severity counts (Safe/Low/Moderate/High) and Category counts (8 categories).
2. Multilingual-E5: Comparison label counts (MATCHED/CHANGED/MISSING) and Hard Negative counts.
"""

import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any

TRAINING_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TRAINING_DIR / "data"
LEGAL_BERT_DIR = DATA_DIR / "legal_bert"
MULTILINGUAL_E5_DIR = DATA_DIR / "multilingual_e5"


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    return records


def generate_report() -> Dict[str, Any]:
    print("==================================================")
    print("CLARIFAI FINE-TUNING SEED DATASET BALANCE REPORT")
    print("==================================================")

    # 1. Legal-BERT Distribution
    lb_train = load_jsonl(LEGAL_BERT_DIR / "train.jsonl")
    lb_val = load_jsonl(LEGAL_BERT_DIR / "validation.jsonl")
    lb_test = load_jsonl(LEGAL_BERT_DIR / "test.jsonl")
    lb_all = lb_train + lb_val + lb_test

    sev_counts = Counter(r["severity"] for r in lb_all)
    cat_counts = Counter(r["category"] for r in lb_all)

    print("\n--- TASK 1: LEGAL-BERT CLAUSE RISK CLASSIFICATION ---")
    print(f"Total Examples: {len(lb_all)} (Train: {len(lb_train)}, Val: {len(lb_val)}, Test: {len(lb_test)})")
    
    print("\nSeverity Distribution:")
    for sev in ["Safe", "Low", "Moderate", "High"]:
        cnt = sev_counts.get(sev, 0)
        pct = (cnt / len(lb_all) * 100) if lb_all else 0
        print(f"  - {sev:<10}: {cnt:>3} ({pct:>5.1f}%)")

    print("\nCategory Distribution (8 Canonical PRD Categories):")
    for cat in [
        "Payment", "Termination", "Renewal", "Confidentiality",
        "Liability", "Intellectual Property", "Privacy", "Dispute Resolution"
    ]:
        cnt = cat_counts.get(cat, 0)
        pct = (cnt / len(lb_all) * 100) if lb_all else 0
        print(f"  - {cat:<24}: {cnt:>3} ({pct:>5.1f}%)")

    # 2. Multilingual-E5 Distribution
    e5_train = load_jsonl(MULTILINGUAL_E5_DIR / "train.jsonl")
    e5_val = load_jsonl(MULTILINGUAL_E5_DIR / "validation.jsonl")
    e5_test = load_jsonl(MULTILINGUAL_E5_DIR / "test.jsonl")
    e5_all = e5_train + e5_val + e5_test

    class_counts = Counter(r["classification"] for r in e5_all)
    hard_neg_count = sum(1 for r in e5_all if r.get("is_hard_negative"))

    print("\n--- TASK 2: MULTILINGUAL-E5 PAIRWISE COMPARISON ---")
    print(f"Total Clause Pairs: {len(e5_all)} (Train: {len(e5_train)}, Val: {len(e5_val)}, Test: {len(e5_test)})")
    
    print("\nPairwise Alignment Classification Distribution:")
    for cls in ["MATCHED", "CHANGED", "MISSING"]:
        cnt = class_counts.get(cls, 0)
        pct = (cnt / len(e5_all) * 100) if e5_all else 0
        print(f"  - {cls:<10}: {cnt:>3} ({pct:>5.1f}%)")

    print(f"\nHard Negatives: {hard_neg_count} ({hard_neg_count / len(e5_all) * 100:.1f}%)")
    print("==================================================")

    return {
        "legal_bert": {
            "total": len(lb_all),
            "severity_counts": dict(sev_counts),
            "category_counts": dict(cat_counts)
        },
        "multilingual_e5": {
            "total": len(e5_all),
            "class_counts": dict(class_counts),
            "hard_negatives": hard_neg_count
        }
    }


if __name__ == "__main__":
    generate_report()
