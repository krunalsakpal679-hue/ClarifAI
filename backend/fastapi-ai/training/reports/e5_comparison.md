# ClarifAI Multilingual-E5 Fine-Tuning & Baseline Comparison Report

**Evaluation Date:** September 25, 2026  
**Phase:** BOOK4-PHASE-09 (Phase 5 - Multilingual-E5 Contrastive Fine-Tuning)  
**Checkpoint Evaluated:** `backend/fastapi-ai/training/checkpoints/e5/v1.0/`  
**Output Vector Dimension:** `768` (Verified UNCHANGED from base model)  
**Selection Decision:** **SELECTED**  

---

## 1. Executive Summary & Selection Decision

**Decision:** `SELECTED`  
**Rationale:** The fine-tuned Multilingual-E5 checkpoint v1.0 reduced false matches from 4 to 3 while increasing overall comparison accuracy from 50.0% to 70.0% and Macro-F1 from 0.4667 to 0.6889. Output dimension verified strictly 768.

### Key High-Level Metric Comparison
| Metric | Untouched Base Model | Fine-Tuned Checkpoint (v1.0) | Absolute Delta | Status |
| :--- | :---: | :---: | :---: | :--- |
| **Vector Dimension** | 768 | 768 | 0 | **VERIFIED UNCHANGED (PASS)** |
| **Overall Accuracy** | 50.00% | 70.00% | +20.00% | IMPROVED |
| **Macro-F1 Score** | 0.4667 | 0.6889 | +0.2222 | IMPROVED |
| **False Matches (Non-MATCHED -> MATCHED)** | 4 | 3 | -1 | REDUCED (DESIRED) |
| **Missed Matches (MATCHED/CHANGED -> MISSING)** | 0 | 0 | +0 | UNCHANGED |

---

## 2. Per-Class Performance Breakdown

| Comparison Class | Support (N) | Baseline F1 | Fine-Tuned Precision | Fine-Tuned Recall | Fine-Tuned F1 | Status / Note |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **MATCHED** | 3 | 0.6000 | 0.5000 | 1.0000 | 0.6667 | SCORED |
| **CHANGED** | 4 | 0.0000 | 1.0000 | 0.2500 | 0.4000 | SCORED |
| **MISSING** | 3 | 0.8000 | 1.0000 | 1.0000 | 1.0000 | SCORED |

---

## 3. Fine-Tuned Model Confusion Matrix (True \ Predicted)

| Ground Truth \ Pred | Pred: MATCHED | Pred: CHANGED | Pred: MISSING | Total |
| :--- | :---: | :---: | :---: | :---: |
| **True: MATCHED** | 3 | 0 | 0 | 3 |
| **True: CHANGED** | 3 | 1 | 0 | 4 |
| **True: MISSING** | 0 | 0 | 3 | 3 |

---

## 4. Test Split Clause-Pair Evaluation Details

| Doc Pair ID | Clause A / B | True Class | Pred Class | Cosine Sim | Target Sim | Match Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `pair_distrib_territory_012` | `v1_c01` / `v2_c01` | **CHANGED** | **MATCHED** | `0.8832` | `0.81` | MISMATCH |
| `pair_distrib_territory_012` | `v1_c02` / `v2_c02` | **CHANGED** | **MATCHED** | `0.9164` | `0.87` | MISMATCH |
| `pair_saas_v1_v2_001` | `v1_c01` / `v2_c01` | **MATCHED** | **MATCHED** | `1.0000` | `1.00` | CORRECT |
| `pair_saas_v1_v2_001` | `v1_c02` / `v2_c02` | **CHANGED** | **CHANGED** | `0.8333` | `0.82` | CORRECT |
| `pair_saas_v1_v2_001` | `v1_c03` / `None` | **MISSING** | **MISSING** | `0.0000` | `0.00` | CORRECT |
| `pair_saas_v1_v2_001` | `v1_c01` / `v2_c02` | **MISSING** | **MISSING** | `0.6390` | `0.25` | CORRECT |
| `pair_lease_draft_final_004` | `v1_c01` / `v2_c01` | **CHANGED** | **MATCHED** | `0.9561` | `0.88` | MISMATCH |
| `pair_lease_draft_final_004` | `v1_c02` / `v2_c02` | **MATCHED** | **MATCHED** | `1.0000` | `1.00` | CORRECT |
| `pair_lease_draft_final_004` | `v1_c03` / `None` | **MISSING** | **MISSING** | `0.0000` | `0.00` | CORRECT |
| `pair_lease_draft_final_004` | `v1_c04` / `v2_c04` | **MATCHED** | **MATCHED** | `1.0000` | `1.00` | CORRECT |

---

## 5. Multilingual Validation Analysis & Limitation Statement

> [!IMPORTANT]
> **Multilingual Validation Finding:**
> All seed clause-pair dataset items in `backend/fastapi-ai/training/data/multilingual_e5/` are currently in English (`language: en`).
> No non-English seed examples exist in Phase 2's dataset.
> In strict accordance with engineering protocol and the PRD, **multilingual validation on non-English pairs was NOT claimed or fabricated**.
> The base checkpoint `intfloat/multilingual-e5-base` natively retains cross-lingual embedding alignments across 100+ languages, but domain-specific non-English legal clause benchmark validation remains a documented limitation until multilingual legal corpora are ingested in a future expansion phase.

---

## 6. Security, Isolation, and Leakage Verification

- **Cross-User Content Leakage:** Training triples and pairs were strictly constrained within individual document pairs (`doc_pair_id`). No cross-document clause mixing across disparate clients or document owners was performed.
- **Data Leakage Isolation:** 100% document-level isolation maintained across train, validation, and test splits with 0% overlap.
- **Qdrant Collection Schema Protection:** Output embedding dimension is verified to be 768. The Qdrant schema remains untouched and strictly compatible.
