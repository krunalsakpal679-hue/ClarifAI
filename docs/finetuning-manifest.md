# ClarifAI Fine-Tuning & Model Versioning Manifest

**Service:** `/backend/fastapi-ai`  
**Role:** AI Pipeline Developer (Developer 3)  
**Date:** September 25, 2026  
**Phase:** BOOK4-PHASE-09 (Model Packaging & AI Pipeline Integration)  
**Git Checkpoint Commit:** `c4726b5`  

---

## 1. Executive Summary

This manifest provides the definitive audit trail for all models within the ClarifAI AI Pipeline, recording base checkpoints, fine-tuned versions, dataset provenance, training hyperparameters, execution hardware, evaluation metrics vs. baseline, and formal production approval statuses.

---

## 2. Model Status Summary Matrix

| Model Identifier | Operational Role | Base Architecture | Active Checkpoint | Dataset Version | Baseline Acc / Macro-F1 | Fine-Tuned Acc / Macro-F1 | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Legal-BERT** | Stage 2 Clause Risk Classification | `nlpaueb/legal-bert-base-uncased` | `legal-bert/v2.0` | `v2.0-atticus` | 25.00% / 0.1000 | **73.68% / 0.7208** | **PRODUCTION-APPROVED** |
| **Multilingual-E5** | Clause Embedding & Pairwise Alignment | `intfloat/multilingual-e5-base` | `multilingual-e5/v1.1` | `v2.0-comprehensive` | 50.00% / 0.4359 | **85.71% / 0.8857** | **PRODUCTION-APPROVED** |
| **BART-base** | Document & Clause Summarization | `facebook/bart-base` | `facebook/bart-base` | N/A (Pre-trained) | N/A | N/A | **BASE** |
| **IndicTrans2** | English $\leftrightarrow$ Hindi Translation | `ai4bharat/indictrans2-en-indic-1B` | `ai4bharat/indictrans2-en-indic-1B` | N/A (Pre-trained) | N/A | N/A | **BASE** |
| **GPT-OSS-20B** | RAG Chatbot, Simplification & Diff Explanation | `openai/gpt-oss-20b` (Groq API) | `openai/gpt-oss-20b` | N/A (Cloud API) | N/A | N/A | **BASE** |

---

## 3. Detailed Model Fine-Tuning Manifests

### 3.1 Legal-BERT (Clause Risk Classification)

* **Model Name:** Legal-BERT Risk Classifier
* **Base Checkpoint:** `nlpaueb/legal-bert-base-uncased`
* **Selected Active Checkpoint:** `backend/fastapi-ai/training/checkpoints/legal-bert/v2.0/`
* **Model Type / Adaptation:** PEFT LoRA Adapter (`r=16, alpha=32, dropout=0.05, target_modules=["query", "key", "value", "dense"], modules_to_save=["classifier"]`) + 4-Class Classification Head
* **Dataset Version:** `v2.0-atticus` (Combined ClarifAI Benchmark + Atticus CUAD commercial contract dataset expansion)
* **Dataset Split Counts:** Train: 570 clauses across 117 contracts, Val: 168 clauses across 28 contracts, Held-Out Test: 19 clauses across 5 contracts (**100% untouched**)
* **Dataset Leakage Verification:** Verified 100% clean document-level isolation (0% cross-split leakage via `leakage_check.py`)
* **Training Configuration:**
  - **Optimizer:** AdamW (`lr=3e-4`, `weight_decay=0.01`)
  - **Scheduler:** CosineAnnealingLR (`eta_min=1e-5`)
  - **Loss Function:** Class-weighted CrossEntropyLoss (`label_smoothing=0.05`, balanced across Safe, Low, Moderate, High)
  - **Epochs:** 6 (Best checkpoint selected at Epoch 4 based on validation Macro-F1 + Accuracy score)
  - **Batch Size:** 16
  - **Max Sequence Length:** 128 tokens
  - **Random Seed:** 42
* **Key Library Versions:** `torch==2.10.0`, `transformers==5.3.0`, `peft==0.14.0`, `safetensors==0.5.2`
* **Hardware Used:** 13th Gen Intel Core i5-13420H (Multi-threaded CPU, 12 threads)
* **Evaluation Metrics (Held-Out Test Set, N=19):**
  - **Baseline Accuracy:** 25.00% $\rightarrow$ **v2.0 Accuracy: 73.68%**
  - **Baseline Macro-F1:** 0.1000 $\rightarrow$ **v2.0 Macro-F1: 0.7208**
  - **Moderate-Risk F1 (Weak Class Focus):** 0.0000 $\rightarrow$ **0.6667** (Resolved & balanced)
  - **High-Risk F1:** 0.0000 $\rightarrow$ **0.7500**
  - **High-Risk Recall:** **100.00%** (Zero High-risk false negatives to Safe)
  - **Severe False Negatives:** 15 $\rightarrow$ **0 High$\rightarrow$Safe misses**
* **Git Commit Hash:** `c4726b5`
* **Status:** **PRODUCTION-APPROVED** (Explicitly selected in Phase 4/5 with verified test metrics).

---

### 3.2 Multilingual-E5 (Semantic Clause Embedding & Pairwise Comparison)

* **Model Name:** Multilingual-E5 Clause Semantic Alignment Model
* **Base Checkpoint:** `intfloat/multilingual-e5-base`
* **Selected Active Checkpoint:** `backend/fastapi-ai/training/checkpoints/multilingual-e5/v1.1/`
* **Model Type / Adaptation:** Full fine-tuned `SentenceTransformer` module with Mean Pooling and L2 Normalization
* **Dataset Version:** `v2.0-comprehensive` (Document-pair non-overlapping benchmark)
* **Dataset Split Counts:** Train: 16 document pairs (48 clause pairs), Val: 4 document pairs (12 clause pairs), Held-Out Test: 7 document pairs (14 clause pairs)
* **Dataset Leakage Verification:** Verified 100% clean document-pair isolation (0% cross-split overlap via `leakage_check.py`)
* **Training Configuration:**
  - **Loss Function:** `CosineSimilarityLoss`
  - **Optimizer:** AdamW (`lr=2e-5`, `weight_decay=0.01`)
  - **Scheduler:** WarmupCosine
  - **Epochs:** 4
  - **Batch Size:** 4
  - **Prefix Format:** `passage: ` for contract clauses, `query: ` for chatbot questions
  - **Calibrated Decision Thresholds:** Matched $\tau_{match} = 0.92$, Changed $\tau_{changed} = 0.40$
  - **Random Seed:** 42
* **Key Library Versions:** `torch==2.10.0`, `sentence-transformers==6.0.0`, `transformers==5.3.0`
* **Hardware Used:** 13th Gen Intel Core i5-13420H (CPU)
* **Evaluation Metrics (Held-Out Test Set, N=7 pairs):**
  - **Baseline Accuracy:** 50.00% $\rightarrow$ **v1.1 Accuracy: 85.71% (Target Met)**
  - **Baseline Macro-F1:** 0.4359 $\rightarrow$ **v1.1 Macro-F1: 0.8857**
  - **False Matches:** 4 $\rightarrow$ **0 (Zero false matches)**
  - **Missed Matches:** 0 $\rightarrow$ **0**
  - **Output Vector Dimension:** Strictly **768** (100% compatible with Qdrant collection vector schema)
* **Git Commit Hash:** `c4726b5`
* **Status:** **PRODUCTION-APPROVED** (Explicitly selected in Phase 5 with verified test metrics).

---

### 3.3 BART-Base (Document Summarization)

* **Model Name:** BART-Base
* **Base Checkpoint:** `facebook/bart-base`
* **Selected Active Checkpoint:** `facebook/bart-base` (Pre-trained HuggingFace baseline)
* **Fine-Tuning Status:** Not fine-tuned in current training cycle.
* **Status:** **BASE**

---

### 3.4 IndicTrans2 (Hindi $\leftrightarrow$ English Translation)

* **Model Name:** IndicTrans2 1B
* **Base Checkpoint:** `ai4bharat/indictrans2-en-indic-1B`
* **Selected Active Checkpoint:** `ai4bharat/indictrans2-en-indic-1B`
* **Fine-Tuning Status:** Not fine-tuned in current training cycle.
* **Status:** **BASE**

---

### 3.5 GPT-OSS-20B (LLM Generation)

* **Model Name:** GPT-OSS-20B (Groq Cloud API)
* **Active Model Identifier:** `openai/gpt-oss-20b`
* **Fine-Tuning Status:** Not fine-tuned in current training cycle (Offloaded Cloud LLM).
* **Status:** **BASE**

---

## 4. Governance & Architecture Boundaries

1. **Two-Stage Hybrid Risk Engine:** Legal-BERT v2.0 operates strictly as Stage 2 following the Stage 1 deterministic rule engine (R001–R014). It does not replace the rule engine.
2. **Qdrant Vector Schema:** Embedding vector dimension remains strictly 768 floats (`DISTANCE = Cosine`).
3. **AI Safety & Severity Privacy:** Legal-BERT classifications output strictly one of four approved discrete labels (`Safe`, `Low`, `Moderate`, `High`). No numeric confidence score is exposed to user-facing payloads (PRD Chapter 16.9).
4. **Per-Clause Failure Isolation:** All inference loops strictly isolate clause-level exceptions, ensuring document analysis never crashes due to a single malformed clause (PRD Chapter 16.5).
