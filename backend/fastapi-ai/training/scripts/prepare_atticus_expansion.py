"""
ClarifAI Atticus Commercial Contract Dataset Extractor & Preprocessor
Extracts a clean, balanced subset of 600-750 real commercial contract clauses
from the Atticus (CUAD) dataset, defensibly maps to ClarifAI risk schema (Safe, Low, Moderate, High),
assigns rule signals (R001-R014), and integrates with existing ClarifAI seed data
using document-level non-overlapping splitting.
Preserves the untouched held-out test split.
"""

import json
import re
import random
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Any, Set, Tuple

random.seed(42)

TRAINING_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TRAINING_DIR / "data"
LEGAL_BERT_DIR = DATA_DIR / "legal_bert"
ATTICUS_RAW_FILE = DATA_DIR / "atticus_raw" / "CUADv1.json"

APPROVED_SEVERITIES = {"Safe": 0, "Low": 1, "Moderate": 2, "High": 3}


def extract_atticus_contracts(max_contracts: int = 120, max_clauses_per_class: int = 200) -> List[Dict[str, Any]]:
    print(f"Reading raw Atticus CUAD from {ATTICUS_RAW_FILE}...")
    with open(ATTICUS_RAW_FILE, "r", encoding="utf-8") as f:
        cuad = json.load(f)

    extracted_by_doc = defaultdict(list)
    seen_hashes: Set[str] = set()
    class_counts = Counter()

    for doc in cuad["data"]:
        doc_title = doc.get("title", "Commercial Contract").strip()
        doc_id = "cuad_" + re.sub(r"[^a-zA-Z0-9]+", "_", doc_title).strip("_")[:50].lower()

        for paragraph in doc.get("paragraphs", []):
            for qa in paragraph.get("qas", []):
                q_text = qa.get("question", "")
                answers = qa.get("answers", [])

                for ans in answers:
                    clause_text = ans.get("text", "").strip()
                    clause_text = re.sub(r"\s+", " ", clause_text).strip()
                    if len(clause_text) < 40 or len(clause_text) > 800:
                        continue

                    h = hashlib.sha256(clause_text.lower().encode("utf-8")).hexdigest()
                    if h in seen_hashes:
                        continue

                    q_lower = q_text.lower()
                    text_lower = clause_text.lower()

                    severity = None
                    category = None
                    rule_findings = []
                    why_flagged = ""

                    # Defensible risk mapping based on PRD Ch. 16.9 rules
                    if "liquidated damages" in q_lower or "termination fee" in text_lower or "liquidated damages" in text_lower:
                        severity = "High"
                        category = "Termination" if "terminat" in text_lower else "Liability"
                        rule_findings = [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}]
                        why_flagged = "Pre-set liquidated damages or early termination penalty."

                    elif "uncapped liability" in q_lower:
                        severity = "High"
                        category = "Liability"
                        rule_findings = [{"rule_id": "R008", "risk_signal": "Unilateral Liability Disclaimer"}]
                        why_flagged = "Uncapped commercial liability exposure."

                    elif "covenant not to sue" in q_lower or "shall not contest" in text_lower or "covenants not to sue" in text_lower:
                        severity = "High"
                        category = "Dispute Resolution"
                        rule_findings = [{"rule_id": "R012", "risk_signal": "Mandatory Binding Arbitration"}]
                        why_flagged = "No-challenge covenant restricting rights to contest validity."

                    elif "ip ownership assignment" in q_lower:
                        if "assigns all" in text_lower or "shall belong exclusively" in text_lower or "sole property" in text_lower:
                            severity = "High"
                            category = "Intellectual Property"
                            rule_findings = [{"rule_id": "R006", "risk_signal": "Broad IP Assignment"}]
                            why_flagged = "Broad assignment of intellectual property rights."
                        else:
                            severity = "Safe"
                            category = "Intellectual Property"
                            rule_findings = []
                            why_flagged = "Standard work product creation assignment."

                    elif "cap on liability" in q_lower or "limitation of liability" in text_lower:
                        severity = "Moderate"
                        category = "Liability"
                        rule_findings = [{"rule_id": "R005", "risk_signal": "Excessive Liability Transfer"}]
                        why_flagged = "Liability capped to historical fees paid under contract."

                    elif "notice period to terminate renewal" in q_lower or "renewal" in q_lower or "automatically renew" in text_lower:
                        severity = "Moderate"
                        category = "Renewal"
                        rule_findings = [{"rule_id": "R001", "risk_signal": "Auto-Renewal"}]
                        why_flagged = "Automatic contract renewal requiring advance written notice."

                    elif "non-compete" in q_lower or "no-solicit of employees" in q_lower or "no-solicit of customers" in q_lower:
                        if "shall not compete" in text_lower or "non-compete" in text_lower or "solicit" in text_lower:
                            severity = "Moderate"
                            category = "Termination"
                            rule_findings = [{"rule_id": "R010", "risk_signal": "Restrictive Non-Compete"}]
                            why_flagged = "Post-termination restrictive non-compete or non-solicitation covenant."

                    elif "audit rights" in q_lower or ("audit" in text_lower and "books and records" in text_lower):
                        severity = "Low"
                        category = "Privacy"
                        rule_findings = []
                        why_flagged = "Routine accounting books and records audit right."

                    elif "termination for convenience" in q_lower or "terminate for convenience" in text_lower:
                        severity = "Moderate"
                        category = "Termination"
                        rule_findings = [{"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}]
                        why_flagged = "Standard commercial termination for convenience."

                    elif "governing law" in q_lower:
                        severity = "Safe"
                        category = "Dispute Resolution"
                        rule_findings = []
                        why_flagged = "Standard governing law and venue selection clause."

                    elif "warranties" in q_lower or "warranty duration" in q_lower:
                        if "disclaims all warranties" in text_lower or "as is" in text_lower:
                            severity = "Moderate"
                            category = "Liability"
                            rule_findings = [{"rule_id": "R008", "risk_signal": "Unilateral Liability Disclaimer"}]
                            why_flagged = "Disclaimer of implied warranties of merchantability."
                        else:
                            severity = "Safe"
                            category = "Liability"
                            rule_findings = []
                            why_flagged = "Standard limited commercial warranty."

                    elif "insurance" in q_lower:
                        severity = "Low"
                        category = "Liability"
                        rule_findings = []
                        why_flagged = "Standard commercial general liability insurance covenant."

                    elif "affiliate license-licensor" in q_lower or "affiliate license-licensee" in q_lower:
                        severity = "Safe"
                        category = "Intellectual Property"
                        rule_findings = []
                        why_flagged = "Standard affiliate licensing permissions."

                    if severity and category:
                        if class_counts[severity] < max_clauses_per_class:
                            seen_hashes.add(h)
                            class_counts[severity] += 1
                            extracted_by_doc[doc_id].append({
                                "clause_id": f"c_{len(extracted_by_doc[doc_id])+1:02d}",
                                "text": clause_text,
                                "clause_text": clause_text,
                                "category": category,
                                "severity": severity,
                                "severity_id": APPROVED_SEVERITIES[severity],
                                "rule_findings": rule_findings,
                                "why_flagged": why_flagged,
                                "metadata": {
                                    "origin": "ATTICUS/CUAD-COMMERCIAL",
                                    "dataset_version": "v2.0-atticus-augmented",
                                    "language": "en"
                                }
                            })

    # Filter documents
    doc_list = []
    for doc_id, clauses in extracted_by_doc.items():
        if clauses:
            doc_list.append({
                "doc_id": doc_id,
                "doc_type": clauses[0].get("doc_type", "Commercial Contract"),
                "clauses": clauses
            })

    random.shuffle(doc_list)
    doc_list = doc_list[:max_contracts]
    return doc_list


def build_augmented_dataset():
    print("==================================================")
    print("Building Atticus-Augmented ClarifAI Dataset (v2.0)")
    print("==================================================")

    # 1. Load existing seed documents
    from generate_comprehensive_dataset import (
        DOCUMENTS_LEGAL_BERT_EXPANDED,
        deduplicate_clauses,
        split_by_document,
        build_legal_bert_examples,
        save_jsonl
    )

    cleaned_seed_docs = deduplicate_clauses(DOCUMENTS_LEGAL_BERT_EXPANDED)
    train_seed, val_seed, test_seed = split_by_document(cleaned_seed_docs, id_key="doc_id", seed=42)

    # 2. Extract Atticus clauses
    atticus_docs = extract_atticus_contracts(max_contracts=120, max_clauses_per_class=175)
    
    # Split Atticus documents strictly into Train (80%) and Validation (20%)
    # Test set remains strictly the original ClarifAI test split!
    n_atticus_train = int(len(atticus_docs) * 0.80)
    train_atticus_docs = atticus_docs[:n_atticus_train]
    val_atticus_docs = atticus_docs[n_atticus_train:]

    print(f"Atticus Documents: Total={len(atticus_docs)} -> Train={len(train_atticus_docs)}, Val={len(val_atticus_docs)}, Test=0 (Protected)")

    # Combine seed + atticus for train and val
    all_train_docs = train_seed + train_atticus_docs
    all_val_docs = val_seed + val_atticus_docs
    all_test_docs = test_seed  # STRICTLY UNTOUCHED

    train_records = build_legal_bert_examples(all_train_docs, "train")
    val_records = build_legal_bert_examples(all_val_docs, "validation")
    test_records = build_legal_bert_examples(all_test_docs, "test")

    save_jsonl(train_records, LEGAL_BERT_DIR / "train.jsonl")
    save_jsonl(val_records, LEGAL_BERT_DIR / "validation.jsonl")
    save_jsonl(test_records, LEGAL_BERT_DIR / "test.jsonl")

    print("\n--- Final Dataset Summary ---")
    print(f"Train Records: {len(train_records)} across {len(all_train_docs)} contracts")
    print(f"Val Records  : {len(val_records)} across {len(all_val_docs)} contracts")
    print(f"Test Records : {len(test_records)} across {len(all_test_docs)} contracts (Untouched)")

    train_dist = Counter(r["severity"] for r in train_records)
    val_dist = Counter(r["severity"] for r in val_records)
    test_dist = Counter(r["severity"] for r in test_records)

    print(f"Train Class Distribution: {dict(train_dist)}")
    print(f"Val Class Distribution  : {dict(val_dist)}")
    print(f"Test Class Distribution : {dict(test_dist)}")


if __name__ == "__main__":
    build_augmented_dataset()
