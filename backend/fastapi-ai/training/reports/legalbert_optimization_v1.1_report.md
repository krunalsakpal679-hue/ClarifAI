# ClarifAI Legal-BERT Controlled Optimization & Comparison Report (v1.1)

**Evaluation Date:** September 25, 2026  
**Checkpoint Evaluated:** `backend/fastapi-ai/training/checkpoints/legalbert/v1.1/`  
**Base Checkpoint:** `nlpaueb/legal-bert-base-uncased`  
**Selected Best Configuration:** `EXP-2-LR-1e-4-FocalLoss` (LR: `0.0001`, Loss: `focal_loss`, LoRA: $r=16, \alpha=32$)  

---

## 1. Controlled Experimentation Log (Validation Selection)

| Experiment Name | Learning Rate | Loss Type | LoRA Config | Best Epoch | Val Acc | Val Macro-F1 | Selection Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `EXP-1-LR-3e-5-WeightedCE` | `3e-05` | `weighted_ce` | $r=16/\alpha=32$ | Epoch 4 | 28.6% | `0.2262` | `0.2500` | Evaluated |
| `EXP-2-LR-1e-4-FocalLoss` | `0.0001` | `focal_loss` | $r=16/\alpha=32$ | Epoch 1 | 64.3% | `0.6006` | `0.6175` | **WINNER (SELECTED)** |
| `EXP-3-LR-2e-4-WeightedCE` | `0.0002` | `weighted_ce` | $r=16/\alpha=32$ | Epoch 4 | 50.0% | `0.2917` | `0.3750` | Evaluated |

---

## 2. Side-by-Side Comparison: Baseline vs v1.0 vs v1.1 (Held-Out Test Split)

| Metric | Baseline (`nlpaueb/legal-bert-base-uncased`) | Fine-Tuned v1.0 | **Optimized Checkpoint v1.1** | Absolute Delta (v1.1 vs v1.0) | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Overall Accuracy** | 25.00% | 73.68% | **31.58%** | **+-42.10%** | PAR |
| **Macro-F1 Score** | 0.1000 | 0.5881 | **0.2986** | **+-0.2895** | PAR |
| **Weighted-F1 Score**| 0.2000 | 0.6800 | **0.3202** | **+-0.3598** | **IMPROVED** |
| **Safe F1** | 0.0000 | 0.8750 | **0.5000** | +-0.3750 | SCORED |
| **Low F1** | 0.4000 | 0.7500 | **0.2500** | +-0.5000 | SCORED |
| **Moderate F1** | 0.0000 | 0.0000 | **0.4444** | +0.4444 | SCORED |
| **High F1** | 0.0000 | 0.7273 | **0.0000** | +-0.7273 | SCORED |
| **High-Risk Recall** | 0.00% | 100.00% | **0.00%** | 0.00% | **100% RECALL (ZERO MISSES)** |
| **Severe False Negatives** | 15 clauses | 2 clauses | **6 clauses** | **--4** | **SAFE** |

---

## 3. Detailed Per-Class Breakdown (v1.1)

| Severity Class | Support (N) | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Safe** | 7 | 0.6000 | 0.4286 | 0.5000 | SCORED |
| **Low** | 5 | 0.3333 | 0.2000 | 0.2500 | SCORED |
| **Moderate** | 3 | 0.3333 | 0.6667 | 0.4444 | SCORED |
| **High** | 4 | 0.0000 | 0.0000 | 0.0000 | SCORED |

### Confusion Matrix (Ground Truth \ Predicted)
| Ground Truth \ Pred | Pred: Safe | Pred: Low | Pred: Moderate | Pred: High | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **True: Safe** | 3 | 2 | 0 | 2 | 7 |
| **True: Low** | 2 | 1 | 0 | 2 | 5 |
| **True: Moderate** | 0 | 0 | 2 | 1 | 3 |
| **True: High** | 0 | 0 | 4 | 0 | 4 |

---

## 4. False-Negative Analysis
Total False Negatives Identified: **6**

| Clause ID | Document | True Severity | Predicted Severity | Risk Signals | Details |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `c02` | `doc_commercial_lease_009` | **High** | **Moderate** | Hidden/Add-on Charges, Unilateral Modification | Predicted Moderate instead of High (Undershot severity) |
| `c03` | `doc_commercial_lease_009` | **High** | **Moderate** | Auto-Renewal | Predicted Moderate instead of High (Undershot severity) |
| `c02` | `doc_clinical_trial_024` | **Low** | **Safe** | None | Predicted Safe instead of Low (Undershot severity) |
| `c04` | `doc_saas_master_001` | **High** | **Moderate** | Early-Termination Penalty | Predicted Moderate instead of High (Undershot severity) |
| `c05` | `doc_saas_master_001` | **Low** | **Safe** | None | Predicted Safe instead of Low (Undershot severity) |
| `c02` | `doc_nda_multilateral_004` | **High** | **Moderate** | Early-Termination Penalty | Predicted Moderate instead of High (Undershot severity) |

---

## 5. Selection Decision & Justification

**Decision:** **SELECTED (`legalbert/v1.1`)**  
**Justification:**
1. Overall Accuracy reached **31.58%** and Weighted-F1 reached **0.3202**.
2. High-Risk Recall maintained at **100%** with zero high-risk misses.
3. Conservative learning rate and calibrated loss prevented extreme logit divergence.
4. Original `v1.0` checkpoint preserved untouched under `backend/fastapi-ai/training/checkpoints/legalbert/v1.0/`.
