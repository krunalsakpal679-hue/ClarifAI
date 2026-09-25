# ClarifAI Multilingual-E5 Controlled Optimization & Comparison Report (v1.1)

**Evaluation Date:** September 25, 2026  
**Checkpoint Evaluated:** `backend/fastapi-ai/training/checkpoints/e5/v1.1/`  
**Output Vector Dimension:** `768` (Verified STRICTLY UNCHANGED)  
**Selected Best Configuration:** `EXP-E5-1-LR-1e-5` (LR: `1e-05`, Thresholds: Matched=0.92, Changed=0.4)  

---

## 1. Controlled Experimentation Log (Validation Selection)

| Experiment Name | Learning Rate | Epochs | Batch Size | Val Acc | Val Macro-F1 | Calibrated Thresholds | Selection Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `EXP-E5-1-LR-1e-5` | `1e-05` | 4 | 4 | 100.0% | `1.0000` | Matched: 0.92, Changed: 0.4 | **WINNER (SELECTED)** |
| `EXP-E5-2-LR-2e-5` | `2e-05` | 4 | 4 | 100.0% | `1.0000` | Matched: 0.9, Changed: 0.4 | Evaluated |
| `EXP-E5-3-LR-3e-5` | `3e-05` | 4 | 4 | 100.0% | `1.0000` | Matched: 0.9, Changed: 0.4 | Evaluated |

---

## 2. Side-by-Side Comparison: Baseline vs v1.0 vs v1.1 (Held-Out Test Split)

| Metric | Baseline (`intfloat/multilingual-e5-base`) | Fine-Tuned v1.0 | **Optimized Checkpoint v1.1** | Absolute Delta (v1.1 vs v1.0) | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Output Vector Dimension** | 768 | 768 | **768** | 0 | **VERIFIED (PASS)** |
| **Overall Accuracy** | 50.00% | 71.43% | **85.71%** | **+14.28%** | IMPROVED |
| **Macro-F1 Score** | 0.4667 | 0.7111 | **0.8857** | **+0.1746** | IMPROVED |
| **False Matches** | 4 | 1 | **0** | -1 | **REDUCED** |
| **Missed Matches** | 0 | 0 | **0** | 0 | **ZERO REGRESSION** |

---

## 3. Per-Class Detailed Performance Breakdown (v1.1)

| Comparison Class | Support (N) | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **MATCHED** | 1 | 1.0000 | 1.0000 | 1.0000 | SCORED |
| **CHANGED** | 3 | 0.7500 | 1.0000 | 0.8571 | SCORED |
| **MISSING** | 3 | 1.0000 | 0.6667 | 0.8000 | SCORED |

### Confusion Matrix (Ground Truth \ Predicted)
| Ground Truth \ Pred | Pred: MATCHED | Pred: CHANGED | Pred: MISSING | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **True: MATCHED** | 1 | 0 | 0 | 1 |
| **True: CHANGED** | 0 | 3 | 0 | 3 |
| **True: MISSING** | 0 | 1 | 2 | 3 |

---

## 4. Test Split Evaluation Details

| Doc Pair ID | Clause A / B | True Class | Pred Class | Cosine Sim | Target Sim | Match Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `pair_saas_v1_v2_001` | `v1_c01` / `v2_c01` | **MATCHED** | **MATCHED** | `1.0000` | `1.00` | CORRECT |
| `pair_saas_v1_v2_001` | `v1_c02` / `v2_c02` | **CHANGED** | **CHANGED** | `0.8619` | `0.75` | CORRECT |
| `pair_saas_v1_v2_001` | `v1_c03` / `None` | **MISSING** | **MISSING** | `0.0000` | `0.10` | CORRECT |
| `pair_saas_v1_v2_001` | `v1_c01` / `v2_c02` | **MISSING** | **CHANGED** | `0.7426` | `0.20` | MISMATCH |
| `pair_nda_unilateral_bilateral_002` | `v1_c01` / `v2_c01` | **CHANGED** | **CHANGED** | `0.9015` | `0.78` | CORRECT |
| `pair_nda_unilateral_bilateral_002` | `v1_c02` / `v2_c02` | **CHANGED** | **CHANGED** | `0.8654` | `0.75` | CORRECT |
| `pair_nda_unilateral_bilateral_002` | `None` / `v2_c03` | **MISSING** | **MISSING** | `0.0000` | `0.10` | CORRECT |

---

## 5. Selection Decision & Justification

**Decision:** **SELECTED (`e5/v1.1`)**  
**Justification:**
1. Test accuracy reached **85.71%** and Macro-F1 reached **0.8857**.
2. Output embedding vector dimension strictly verified as 768.
3. Zero missed matches on held-out test data.
4. Original `v1.0` checkpoint preserved untouched under `backend/fastapi-ai/training/checkpoints/e5/v1.0/`.
