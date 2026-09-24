# ClarifAI AI Model Fine-Tuning Audit & Baseline Environment Report

**Document Version:** 1.0.0  
**Date:** September 24, 2026  
**Author / Role:** AI Pipeline Developer (Developer 3)  
**Branch:** `feature/ai-model-finetuning`  
**Primary Source of Truth:** ClarifAI PRD v2.3 (Chapters 16.9, 17.7, 28.1, 44, 50)  
**Implementation Source of Truth:** `/backend/fastapi-ai/`  

---

## 1. Executive Summary

This report documents the baseline audit and inspection of the ClarifAI AI microservice (`/backend/fastapi-ai`) prior to any fine-tuning activities. The audit verifies the exact currently-loaded model checkpoints for **Legal-BERT** and **Multilingual-E5**, confirms the complete absence of local training datasets in the repository, records real hardware detection benchmarks, and documents container runtime and Git LFS statuses.

Per project scope, generation LLM **GPT-OSS-20B** (via Groq Cloud API) is operational, external, and strictly out of scope for local fine-tuning.

---

## 2. Legal-BERT Current State

| Attribute | Inspected / Verified Specification |
| :--- | :--- |
| **Model Role** | Stage 2 of the two-stage hybrid risk analysis pipeline (PRD Chapter 16.9). Receives clause text and deterministic rule findings (R001–R014) to classify clause risk severity. |
| **Loaded Checkpoint Identifier** | `nlpaueb/legal-bert-base-uncased` (configured via `LEGAL_BERT_MODEL_NAME` env var; default `nlpaueb/legal-bert-base-uncased`). |
| **Fine-Tuning Status** | **BASE / INTERIM PLACEHOLDER** (Not fine-tuned; base pretrained weights loaded directly). |
| **Label Set / Output Shape** | Strict 4-level severity classification: `0: "Safe"`, `1: "Low"`, `2: "Moderate"`, `3: "High"`. `num_labels = 4`, output logit tensor shape `[batch_size, 4]`. |
| **Tokenizer** | `AutoTokenizer.from_pretrained("nlpaueb/legal-bert-base-uncased")` (BERT WordPiece uncased vocabulary). |
| **Model Architecture** | `AutoModelForSequenceClassification` with linear classification head (110M parameters). |
| **Weight Loading Source** | Hugging Face Model Hub (downloaded and cached dynamically to `HF_HOME` / local Hugging Face cache; no local custom weight directory exists). |
| **FastAPI Integration Points** | **Service:** [risk_service.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/app/services/risk_service.py) (`load_legal_bert_model()`, `classify_clause_risk()`, `classify_document_clauses_risk()`).<br>**Router:** [risk.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/app/routers/risk.py) (`POST /api/v1/classify-risk`, `POST /api/v1/classify-document-risk`).<br>**Validators:** [output_validator_service.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/app/services/output_validator_service.py) (`validate_and_resolve_clause_risk()`). |

---

## 3. Multilingual-E5 Current State

| Attribute | Inspected / Verified Specification |
| :--- | :--- |
| **Model Role** | Dense vector embedding generation for clause storage in Qdrant, evidence retrieval in RAG chatbot, and pairwise clause similarity matching (PRD Chapters 17.7, 28.1, 28.4, 28.5, Decision R-05). |
| **Loaded Checkpoint Identifier** | `intfloat/multilingual-e5-base` (configured via `EMBEDDING_MODEL_NAME` env var; default `intfloat/multilingual-e5-base`). |
| **Fine-Tuning Status** | **BASE / INTERIM PLACEHOLDER** (Not fine-tuned; base pretrained weights loaded directly). |
| **Vector Output Shape & Dimension** | Dense 768-dimensional float embedding vector (`List[float]` of length 768, normalized for cosine similarity distance metric). |
| **Prefix Protocol** | Required E5 asymmetric prefixes: `"passage: "` for clause/document indexing, `"query: "` for RAG search/similarity queries. |
| **Sequence Length Constraint** | Max sequence length: `512` tokens (`MAX_SEQUENCE_LENGTH = 512`). Clauses fit directly without chunking (avg 50–300 tokens). |
| **Tokenizer / Framework** | `sentence_transformers.SentenceTransformer` wrapping XLM-RoBERTa base architecture (278M parameters). |
| **Weight Loading Source** | Hugging Face Model Hub (downloaded and cached dynamically; no local custom weight directory exists). |
| **FastAPI Integration Points** | **Service:** [embedding_service.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/app/services/embedding_service.py) (`get_embedding_model()`, `generate_clause_embedding()`, `generate_query_embedding()`, `generate_batch_embeddings()`).<br>**Router:** [embedding.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/app/routers/embedding.py) (`POST /api/v1/generate-embedding`, `POST /api/v1/generate-embeddings`).<br>**Vector Store:** [qdrant_service.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/app/services/qdrant_service.py) (`index_document_clauses()`, `query_clauses_scoped()`).<br>**Comparison:** [comparison_service.py](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/app/services/comparison_service.py) (`compare_documents()`). |

---

## 4. Existing Dataset(s) Found

A comprehensive recursive search was executed across the entire repository for tabular, structured, or annotated datasets (`*.csv`, `*.jsonl`, `*.parquet`, `*.tsv`, `*.arrow`, `/data`, `/dataset`, or Hugging Face dataset loading scripts).

| Task / Objective | Search Target | Status / Finding | Details |
| :--- | :--- | :---: | :--- |
| **Task 1: Clause Risk & Category Classification** | Labeled clauses with ground-truth severity (*High, Moderate, Low, Safe*) and category (*Payment, Termination, Renewal, Confidentiality, Liability, IP, Privacy, Dispute Resolution*). | **NOT FOUND** | Zero labeled dataset files, annotations, or data loaders exist in the repository. |
| **Task 2: Pairwise Clause Comparison** | Document pairs with clause alignments, similarity ratings, and span difference classifications (*MATCHED, CHANGED, MISSING*). | **NOT FOUND** | Zero contract pairing datasets, diff corpora, or span annotations exist in the repository. |
| **Data Directories & Loaders** | `/data`, `/dataset`, or `datasets.load_dataset` code paths. | **NOT FOUND** | No training data directories or ingestion pipelines exist in the repository. |

*Conclusion: Both models currently operate strictly with base pretrained weights and synthetic test fixtures.*

---

## 5. Hardware Detected

Hardware specifications were detected via automated runtime inspection (`torch`, `psutil`, `shutil`, `platform`, and `nvidia-smi`):

```text
PYTHON_VERSION=3.14.3
OS=Windows 11 (10.0.26200)
PROCESSOR=Intel64 Family 6 Model 186 Stepping 2, GenuineIntel
CPU_LOGICAL_CORES=12
CPU_PHYSICAL_CORES=8
RAM_TOTAL_GB=15.71
DISK_FREE_GB=21.31
DISK_TOTAL_GB=275.06
CUDA_AVAILABLE=False
GPU_COUNT=0
GPU_NAME=None
GPU_VRAM_GB=0.0
```

### 5.1 Physical Hardware vs. Active Python Environment Breakdown

| Component | Physical Host Specification | Active Python Runtime State | Implications for Fine-Tuning |
| :--- | :--- | :--- | :--- |
| **CPU** | 13th Gen Intel(R) Core(TM) i5-13420H (8 physical cores, 12 logical processors) | Fully accessible (12 logical cores) | Sufficient for CPU inference and lightweight data preprocessing. CPU fine-tuning will be slow. |
| **System RAM** | 16.00 GB DDR5 (15.71 GB usable) | 15.71 GB available | Adequate for base model batch inference and dataset tokenization. |
| **Discrete GPU** | **NVIDIA GeForce RTX 4050 Laptop GPU** (6141 MiB / ~6.0 GB GDDR6 VRAM, Driver 546.18, CUDA 12.3 supported) | **Not currently utilized** (`torch.cuda.is_available() == False` due to `torch==2.10.0+cpu` build in active environment) | Enabling CUDA PyTorch will unlock 6 GB VRAM for accelerated fine-tuning (e.g. LoRA, QLoRA, or fp16 head tuning). |
| **Free Disk Space** | **21.31 GB Free** on Drive `C:\` (275.06 GB total) | 21.31 GB Free | Sufficient for base checkpoints (~1.5 GB total) and small fine-tuning datasets (<500 MB). Checkpoint checkpoints must be pruned to avoid disk exhaustion. |

---

## 6. Docker / GPU Container Status

| Attribute | Inspected Status |
| :--- | :--- |
| **Docker Engine** | `Docker version 29.7.2, build a7dcaa6` (Active, WSL2 backend). |
| **Docker Compose** | `v5.4.0` (Active). |
| **FastAPI Base Image** | `python:3.11-slim` ([Dockerfile](file:///c:/ClarifAI-%20AIPipeline/backend/fastapi-ai/Dockerfile)). |
| **Container GPU Support** | **CPU-ONLY** (No `nvidia-docker`, CUDA base image, or GPU runtime arguments configured in `Dockerfile`). |
| **Weight Baking Policy** | Weights are **NOT** baked into image layers; models are downloaded at container startup or mounted via host volume (`HF_HOME`). |

---

## 7. Git LFS Status

| Attribute | Inspected Status |
| :--- | :--- |
| **Git LFS CLI** | `git-lfs/3.7.1` installed on host system. |
| **Repository `.gitattributes`** | **NOT CONFIGURED** (No `.gitattributes` file exists in the repository). |
| **LFS Tracking** | No file types or paths (`*.bin`, `*.safetensors`, `*.pt`, `*.onnx`) are currently tracked via Git LFS. |

---

## 8. Summary Table & Next Phase Readiness

| Audit Dimension | Verified Baseline State | Action for Subsequent Phases |
| :--- | :--- | :--- |
| **Legal-BERT** | Base `nlpaueb/legal-bert-base-uncased` (Interim) | Prepare domain dataset & fine-tuning strategy. |
| **Multilingual-E5** | Base `intfloat/multilingual-e5-base` (Interim) | Prepare contract retrieval dataset & evaluation pairs. |
| **Labeled Data** | **NOT FOUND** (0 datasets exist) | Synthetic / curated legal domain dataset creation required in Phase 2. |
| **Hardware / GPU** | RTX 4050 GPU (6 GB VRAM) physically present; CPU PyTorch active. | Enable CUDA PyTorch or plan LoRA/CPU-safe training budget. |
| **Disk Headroom** | 21.31 GB Free | Monitor checkpoint size during training. |
| **Git LFS** | Not initialized | Configure `.gitattributes` if committing custom model weights. |
