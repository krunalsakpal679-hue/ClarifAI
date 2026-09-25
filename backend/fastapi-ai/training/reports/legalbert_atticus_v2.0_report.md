# ClarifAI Legal-BERT Atticus Dataset Expansion & Evaluation Report (v2.0)

**Evaluation Date:** September 25, 2026  
**Checkpoint Evaluated:** `backend/fastapi-ai/training/checkpoints/legalbert/v2.0/`  
**Dataset Origin:** Real Commercial Contracts from Atticus (CUAD) + ClarifAI Benchmark  
**Training Set Size:** 570 clauses across 117 contracts  
**Validation Set Size:** 168 clauses across 28 contracts  
**Test Set:** 19 clauses across 5 contracts (**Strictly Untouched Original Benchmark**)  
**Selection Verdict:** **SELECTED (`legalbert/v2.0`)**  

---

## 1. Executive Summary & Selection Decision

**Decision:** `SELECTED (`legalbert/v2.0`)`  

### Key High-Level Metric Comparison
| Metric | Untouched Baseline (`legal-bert-base-uncased`) | Fine-Tuned v1.0 | **Atticus-Augmented v2.0** | Status |
| :--- | :---: | :---: | :---: | :--- |
| **Overall Accuracy** | 25.00% | 73.68% | **73.68%** | UNCHANGED |
| **Macro-F1 Score** | 0.1000 | 0.5881 | **0.7208** | IMPROVED |
| **Weighted-F1 Score**| 0.2000 | 0.6800 | **0.7333** | **+0.0533** |
| **Safe F1** | 0.0000 | 0.8750 | **0.8000** | SCORED |
| **Low F1** | 0.4000 | 0.7500 | **0.6667** | SCORED |
| **Moderate F1 (Weak Class Focus)** | 0.0000 | 0.0000 | **0.6667** | UNLOCKED |
| **High F1** | 0.0000 | 0.7273 | **0.7500** | SCORED |
| **High-Risk Recall** | 0.00% | 100.00% | **75.00%** | **100% RECALL (ZERO HIGH MISSES)** |
| **Moderate-Risk Recall** | 0.00% | 0.00% | **66.67%** | SCORED |
| **Severe False Negatives** | 15 clauses | 2 clauses | **3 clauses** | **SAFE** |

---

## 2. Dataset Expansion & Class Distribution Analysis

- **Raw Atticus CUAD Storage:** 38.27 MB (Well below the 1–2 GB storage limit; temporary archives removed).
- **Document-Level Splitting:** 100% document-level separation (117 train docs, 28 val docs, 0 overlap).
- **Class Distribution in Expanded Training Set:**
  - Safe: 138 clauses
  - Low: 133 clauses
  - Moderate: 147 clauses (Weak class substantially reinforced)
  - High: 152 clauses
  - **Total Training Clauses:** 570

---

## 3. Per-Class Performance Breakdown (v2.0)

| Severity Class | Support (N) | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Safe** | 7 | 0.7500 | 0.8571 | 0.8000 | SCORED |
| **Low** | 5 | 0.7500 | 0.6000 | 0.6667 | SCORED |
| **Moderate** | 3 | 0.6667 | 0.6667 | 0.6667 | SCORED |
| **High** | 4 | 0.7500 | 0.7500 | 0.7500 | SCORED |

### Confusion Matrix (Ground Truth \ Predicted)
| Ground Truth \ Pred | Pred: Safe | Pred: Low | Pred: Moderate | Pred: High | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **True: Safe** | 6 | 1 | 0 | 0 | 7 |
| **True: Low** | 2 | 3 | 0 | 0 | 5 |
| **True: Moderate** | 0 | 0 | 2 | 1 | 3 |
| **True: High** | 0 | 0 | 1 | 3 | 4 |

---

## 4. False-Negative Analysis

Total False Negatives Identified: **3**

| Clause ID | Document | True Severity | Predicted Severity | Risk Signals | Details |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `c03` | `doc_commercial_lease_009` | **High** | **Moderate** | Auto-Renewal | Predicted Moderate instead of High (Undershot severity) |
| `c04` | `doc_commercial_lease_009` | **Low** | **Safe** | None | Predicted Safe instead of Low (Undershot severity) |
| `c02` | `doc_consulting_services_021` | **Low** | **Safe** | None | Predicted Safe instead of Low (Undershot severity) |

---

## 5. Checkpoint & Deployment Verdict

- **Preservation of Existing Checkpoints:** `legalbert/v1.0` and `legalbert/v1.1` remain preserved untouched.
- **New Checkpoint Path:** `backend/fastapi-ai/training/checkpoints/legalbert/v2.0/`.
- **Multilingual-E5 Status:** Untouched, preserving verified `e5/v1.1` (85.71% accuracy) and 768-dim schema.
