# Dataset Versioning Record

## Active Dataset: `v1.0-comprehensive` (Current Active)
- **Release Date:** September 24, 2026
- **Origin:** Curated High-Precision Domain-Specific Synthetic Seed Dataset for ClarifAI Fine-Tuning & Validation
- **Legal-BERT Examples:** 76 verified clauses across 25 source documents
  - **Train:** 50 clauses (17 documents)
  - **Validation:** 10 clauses (3 documents)
  - **Test:** 16 clauses (5 documents)
  - **Class Distribution:** Safe: 28 (36.8%), Low: 12 (15.8%), Moderate: 17 (22.4%), High: 19 (25.0%)
  - **Category Coverage:** All 8 canonical PRD categories (Payment, Termination, Renewal, Confidentiality, Liability, IP, Privacy, Dispute Resolution)
  - **Rule Engine Context:** Includes mapped rule signals (R001–R014) in `[CLS] ... [SEP] Rule Findings: ... [SEP]` format
- **Multilingual-E5 Examples:** 42 clause comparison pairs across 16 document comparison pairs
  - **Train:** 29 pairs (11 document pairs)
  - **Validation:** 4 pairs (2 document pairs)
  - **Test:** 9 pairs (3 document pairs)
  - **Classification Distribution:** MATCHED: 8 (19.0%), CHANGED: 26 (61.9%), MISSING: 8 (19.0%)
  - **Hard Negatives:** 2 cross-clause distractors included for discriminative fine-tuning
- **Split Distribution Strategy:** 70% Train / 15% Validation / 15% Test (Split **strictly at document level** to guarantee 0 data leakage)
- **Data Leakage Status:** **0 Violations** (Verified by [leakage_check.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/training/scripts/leakage_check.py))
- **Test Integrity:** 5/5 PyTest Unit Tests Passed ([test_training_data_integrity.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/tests/test_training_data_integrity.py))

---

## Historical Releases
### `v0.1-seed`
- **Release Date:** September 24, 2026
- **Origin:** Pipeline validation baseline (57 clauses, 35 comparison pairs).
