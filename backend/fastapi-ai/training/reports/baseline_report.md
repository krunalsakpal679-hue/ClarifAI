# ClarifAI Untouched Base Models Baseline Evaluation Report

**Evaluation Date:** September 25, 2026  
**Status:** COMPLETE (Untouched Baseline Reference Established)  
**Methodology:** Executed end-to-end against production inference code paths (`app/services/risk_service.py`, `app/services/embedding_service.py`, and `app/services/comparison_service.py`) without modifying either model.

---

## 1. Task 1: Legal-BERT Multi-Class Risk Classification Baseline

### 1.1 Model & Test Configuration
- **Model Checkpoint:** `nlpaueb/legal-bert-base-uncased` (Pre-trained Base, un-finetuned classification head)
- **Evaluation Split:** `backend/fastapi-ai/training/data/legal_bert/test.jsonl`
- **Total Test Examples:** 20 clauses (100% document-isolated from training split)
- **Overall Accuracy:** **25.00%** (5/20 correct)
- **Macro-F1:** **0.1000**

### 1.2 Per-Class Performance Breakdown
| Severity Class | Support (N) | Precision | Recall | F1-Score | Status / Note |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Safe** | 7 | 0.0000 | 0.0000 | 0.0000 | SCORED |
| **Low** | 5 | 0.2500 | 1.0000 | 0.4000 | SCORED |
| **Moderate** | 4 | 0.0000 | 0.0000 | 0.0000 | SCORED |
| **High** | 4 | 0.0000 | 0.0000 | 0.0000 | SCORED |

*Note: Classes with $\le 1$ test sample are explicitly tagged as `INSUFFICIENT DATA` to avoid distorted generalization metrics.*

### 1.3 Confusion Matrix (True \ Predicted)
| Ground Truth \ Pred | Pred: Safe | Pred: Low | Pred: Moderate | Pred: High |
| :--- | :---: | :---: | :---: | :---: |
| **True: Safe** | 0 | 7 | 0 | 0 |
| **True: Low** | 0 | 5 | 0 | 0 |
| **True: Moderate** | 0 | 4 | 0 | 0 |
| **True: High** | 0 | 4 | 0 | 0 |

---

## 2. Task 2: Multilingual-E5 Pairwise Contract Comparison Baseline

### 2.1 Model & Test Configuration
- **Model Checkpoint:** `intfloat/multilingual-e5-base` (Pre-trained Base)
- **Evaluation Split:** `backend/fastapi-ai/training/data/multilingual_e5/test.jsonl`
- **Total Test Pairs:** 10 clause comparison pairs
- **Production Similarity Thresholds:** `MATCHED` $\ge 0.88$, `CHANGED` $\ge 0.65$, `MISSING` $< 0.65$
- **Overall Accuracy:** **50.00%** (5/10 correct)
- **Macro-F1:** **0.4667**
- **False Matches (Non-MATCHED classified as MATCHED):** **4**
- **Missed Matches (MATCHED/CHANGED missed as MISSING):** **0**

### 2.2 Per-Class Performance Breakdown
| Alignment Class | Support (N) | Precision | Recall | F1-Score | Status / Note |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **MATCHED** | 3 | 0.4286 | 1.0000 | 0.6000 | SCORED |
| **CHANGED** | 4 | 0.0000 | 0.0000 | 0.0000 | SCORED |
| **MISSING** | 3 | 1.0000 | 0.6667 | 0.8000 | SCORED |

### 2.3 Confusion Matrix (True \ Predicted)
| Ground Truth \ Pred | Pred: MATCHED | Pred: CHANGED | Pred: MISSING |
| :--- | :---: | :---: | :---: |
| **True: MATCHED** | 3 | 0 | 0 |
| **True: CHANGED** | 4 | 0 | 0 |
| **True: MISSING** | 0 | 1 | 2 |

---

## 3. Key Observations & Fine-Tuning Guidance

1. **Legal-BERT Zero-Shot Classification**:
   - The un-finetuned sequence classification head of `nlpaueb/legal-bert-base-uncased` lacks calibrated severity boundaries, yielding baseline macro-F1 of **0.1000**.
   - Fine-tuning in Phase 3 must train the classification head with cross-entropy loss, class weighting for imbalanced severities, and mapped deterministic rule findings features to achieve target macro-F1 $\ge 0.85$.

2. **Multilingual-E5 Semantic Alignment**:
   - The pre-trained `intfloat/multilingual-e5-base` demonstrates strong baseline semantic similarity for verbatim `MATCHED` pairs (similarity $= 1.0$) and distinct `MISSING` additions ($< 0.65$), achieving baseline macro-F1 of **0.4667**.
   - Subtle modification distinction (`CHANGED` vs hard negative distractors) can be enhanced via contrastive fine-tuning (MultipleNegativesRankingLoss / TripletLoss).

---

## 4. Determinism Verification
- Executed consecutive deterministic evaluation passes across both models.
- **Result:** Exact match in all predictions, logits, cosine similarities, and confusion matrix cell counts across iterations.
