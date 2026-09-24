# ClarifAI Model Fine-Tuning Datasets (`training/data/`)

**Dataset Version:** `v0.1-seed`  
**Phase:** AI-PHASE-DATA-SEED-01  
**Primary Source of Truth:** ClarifAI PRD v2.3 (Chapters 16.9, 17.7, 18, 23, 28.1, 50)  

---

## 1. Dataset Overview & Scope Limitation

> [!IMPORTANT]
> **SEED / SYNTHETIC DATASET NOTICE:**
> As confirmed in `/docs/finetuning-audit-report.md`, no production or historical human-annotated contract datasets existed in the repository (**NOT FOUND**). To enable pipeline validation, schema verification, and training harness execution without blocking development, this directory provides a curated **synthetic seed dataset** (`v0.1-seed`).
> 
> - Every record is explicitly tagged with `metadata.origin = "SEED/SYNTHETIC"`.
> - This dataset is intended for **pipeline validation and integration testing**, not as a final production-grade legal benchmark.
> - No private, client, or unapproved user documents were used in generating this data.

---

## 2. Task 1: Legal-BERT Clause Risk Classification (`training/data/legal_bert/`)

### 2.1 Purpose & Role
Fine-tunes or evaluates `nlpaueb/legal-bert-base-uncased` for Stage 2 of the hybrid risk classification pipeline (PRD Chapter 16.9), incorporating both the raw clause text and the deterministic risk signals emitted by Stage 1 Rule Engine (R001–R014).

### 2.2 Input & Contextual Framing Format
```json
{
  "doc_id": "doc_saas_master_001",
  "doc_type": "SaaS Subscription Agreement",
  "clause_id": "c04",
  "clause_text": "Early termination by Customer prior to term expiration shall incur an immediate liquidated penalty equal to 100% of remaining contract value.",
  "rule_findings": [
    {"rule_id": "R002", "risk_signal": "Early-Termination Penalty"}
  ],
  "context_text": "[CLS] Early termination by Customer prior to term expiration shall incur an immediate liquidated penalty equal to 100% of remaining contract value. [SEP] Rule Findings: R002 (Early-Termination Penalty) [SEP] Document Type: SaaS Subscription Agreement [SEP]",
  "severity": "High",
  "severity_id": 3,
  "category": "Termination",
  "why_flagged": "Severe 100% early termination fee penalty.",
  "split": "train",
  "metadata": {
    "origin": "SEED/SYNTHETIC",
    "dataset_version": "v0.1-seed",
    "language": "en"
  }
}
```

### 2.3 Label Spaces
- **Severity (4 Levels):**
  - `0`: `"Safe"`
  - `1`: `"Low"`
  - `2`: `"Moderate"`
  - `3`: `"High"`
- **Approved Categories (8 PRD Canonical Categories):**
  - `Payment`, `Termination`, `Renewal`, `Confidentiality`, `Liability`, `Intellectual Property`, `Privacy`, `Dispute Resolution`

---

## 3. Task 2: Multilingual-E5 Pairwise Clause Comparison (`training/data/multilingual_e5/`)

### 3.1 Purpose & Role
Fine-tunes or evaluates `intfloat/multilingual-e5-base` (768-dimensional dense embeddings) for clause alignment and similarity matching between baseline (Document A) and revised (Document B) contracts (PRD Chapter 18 and Chapter 28.5).

### 3.2 Pairwise Record Format
```json
{
  "doc_pair_id": "pair_saas_v1_v2_001",
  "doc_a_id": "doc_saas_v1",
  "doc_b_id": "doc_saas_v2",
  "contract_title": "SaaS Subscription Agreement (Baseline vs Revised)",
  "clause_a_id": "v1_c02",
  "clause_b_id": "v2_c02",
  "text_a": "Either party may terminate this agreement upon 30 days written notice.",
  "text_b": "Either party may terminate this agreement upon sixty (60) days written notice.",
  "e5_text_a": "passage: Either party may terminate this agreement upon 30 days written notice.",
  "e5_text_b": "passage: Either party may terminate this agreement upon sixty (60) days written notice.",
  "classification": "CHANGED",
  "target_similarity": 0.82,
  "difference_explanation": "Termination notice period increased from 30 days to 60 days.",
  "is_hard_negative": false,
  "split": "train",
  "metadata": {
    "origin": "SEED/SYNTHETIC",
    "dataset_version": "v0.1-seed",
    "language": "en"
  }
}
```

### 3.3 Classification Space
- `MATCHED`: Identical or semantically equivalent clause ($similarity \ge 0.88$).
- `CHANGED`: Modified clause with substantive contractual difference ($0.65 \le similarity < 0.88$).
- `MISSING`: Clause added in B or removed in A, or hard negative distractor ($similarity < 0.65$).

---

## 4. Document-Level Splitting & Leakage Prevention Protocol

1. **Document-Level Grouping:** Every clause or pair from the same `doc_id` or `doc_pair_id` is assigned strictly to **ONE** partition (`train`, `validation`, or `test`). No clauses from the same document span across multiple splits.
2. **Split Ratios:** 70% Train, 15% Validation, 15% Test.
3. **Automated Verification:** Verified by `training/scripts/leakage_check.py` to guarantee:
   $$\text{Train Documents} \cap \text{Val Documents} = \emptyset$$
   $$\text{Train Documents} \cap \text{Test Documents} = \emptyset$$
   $$\text{Val Documents} \cap \text{Test Documents} = \emptyset$$
