# AI Environment Inspection & Hardware Feasibility Report

**Service:** `/backend/fastapi-ai`  
**Role:** AI Pipeline Developer (Developer 3)  
**Project:** ClarifAI  
**Date:** August 23, 2026  
**Status:** Completed (Docker Verification Confirmed)  

---

## 1. Executive Summary

This report documents the machine and local runtime environment inspection for the `/backend/fastapi-ai` service of the ClarifAI project. The inspection covers installed developer tooling (Python, Git, Docker, Antigravity IDE), local AI/ML runtime packages (PyTorch, Transformers, Tesseract), hardware capabilities (CPU, RAM, GPU VRAM), per-model execution classifications (Local vs. API), and end-to-end Docker Desktop/Compose verification.

---

## 2. Tools & Environment Inventory

| Tool / Dependency | Installed Version / Status | Required Action / Notes |
| :--- | :--- | :--- |
| **Python** | `Python 3.14.3` (Default in PATH)<br>`Python 3.13.2` & `Python 3.12.7` (Also present) | **Compatibility Note:** Python 3.12.7 is available as a stable fallback for PyTorch/Transformers binary wheels if Python 3.14 encounters C-extension friction. |
| **Git** | `git version 2.53.0.windows.1` | **Configured:**<br>• `user.name`: `Krunal`<br>• `user.email`: `krunalsakpal679@gmail.com`<br>• *Repository status:* Workspace root `c:\ClarifAI- AIPipeline` is clean / uninitialized. |
| **Docker Desktop** | `Docker CLI 29.7.2`<br>`Docker Desktop v4.87.0` | **Daemon Status: ACTIVE & RUNNING**.<br>Connected via WSL2 engine (`Kernel 6.6.87.2-microsoft-standard-WSL2`). Server Version `29.7.2`. |
| **Docker Compose** | `v5.4.0` | **Installed & Active** (`docker compose version` verified). |
| **Antigravity IDE** | Active (`v1.x`) | Connected to workspace `c:\ClarifAI- AIPipeline`. Execution environment and tooling reachability confirmed functional. |

---

## 3. Hardware Specifications Detection

| Hardware Component | Detected Specification |
| :--- | :--- |
| **CPU** | `13th Gen Intel(R) Core(TM) i5-13420H` (8 Physical Cores, 12 Logical Processors) |
| **System Memory (RAM)** | `16.00 GB` (17,179,869,184 Bytes) |
| **Discrete GPU** | **NVIDIA GeForce RTX 4050 Laptop GPU** |
| **VRAM** | `6141 MiB` (~6.0 GB GDDR6) |
| **NVIDIA Driver Version** | `546.18` |
| **CUDA Version Support** | `CUDA 12.3` (via Driver) |
| **Integrated GPU** | Intel(R) UHD Graphics (Shared Memory) |
| **Available Disk Space** | `20.80 GB Free` on Drive `C:\` (Total Capacity: 275.06 GB) |

---

## 4. Local AI/ML Runtime Dependencies

| Runtime / Package | Installed Version | Location / Findings |
| :--- | :--- | :--- |
| **PyTorch** | `2.10.0+cpu` | Installed under `AppData\Roaming\Python\Python314\site-packages`.<br>**CRITICAL FINDING:** Installed PyTorch is CPU-only (`CUDA available: False`). PyTorch with CUDA 12.1/12.4 support must be re-installed to utilize the RTX 4050 GPU. |
| **Transformers** | `4.38.1` | Installed under `Python312\site-packages` (with `huggingface_hub` `0.36.2`, `tokenizers` `0.15.2`, `safetensors` `0.7.0`). |
| **FastAPI** | `0.110.0` | Installed under `Python312\site-packages` (with `pydantic` `2.6.1`, `uvicorn` `0.27.1`). |
| **Tesseract OCR CLI** | `v5.4.0.20240606` | **Installed at:** `C:\Program Files\Tesseract-OCR\tesseract.exe`.<br>**FINDING:** Installed, but directory `C:\Program Files\Tesseract-OCR` is **NOT in Windows PATH**. `pytesseract` `0.3.10` is installed. |

---

## 5. Model Inventory & Execution Classification

| Model Name | Standard Model Identifier | Execution Mode | Hardware Requirement & Feasibility |
| :--- | :--- | :--- | :--- |
| **Legal-BERT** | `nlpaueb/legal-bert-base-uncased` | **Local** (PyTorch / Transformers) | ~440 MB weights. Feasible on CPU / GPU. Marked as **FEASIBILITY CHECK** for `AI-FEASIBILITY-01`. |
| **BART-base** | `facebook/bart-base` | **Local** (PyTorch / Transformers) | ~500 MB weights. Feasible on CPU / GPU for summarization. Marked as **FEASIBILITY CHECK** for `AI-FEASIBILITY-01`. |
| **Multilingual-E5** | `intfloat/multilingual-e5-small` / `base` | **Local** (Sentence-Transformers / PyTorch) | ~470 MB to 1.1 GB weights for document embeddings. Feasible on CPU / GPU. Marked as **FEASIBILITY CHECK** for `AI-FEASIBILITY-01`. |
| **Llama 3.1 8B** | Cloud API via Groq | **API-based** (Groq SDK / REST API) | **No local GPU VRAM required.** Offloaded to Groq cloud inference engine. Requires valid `GROQ_API_KEY`. |
| **Tesseract OCR** | Native Binary (`tesseract.exe`) | **Local** (Native C++ Binary) | Runs on CPU. Binary exists at `C:\Program Files\Tesseract-OCR\tesseract.exe`. Requires PATH configuration. |

---

## 6. Docker Verification & Functionality Confirmation

| Verification Step | Command Executed | Output / Finding | Result |
| :--- | :--- | :--- | :--- |
| **Docker CLI Version** | `docker --version` | `Docker version 29.7.2, build a7dcaa6` | **PASSED** |
| **Docker Compose Version** | `docker compose version` | `Docker Compose version v5.4.0` | **PASSED** |
| **Docker Daemon Status** | `docker info` | `Server Version: 29.7.2`, Docker Desktop 4.87.0 (WSL2 Kernel `6.6.87.2`) | **PASSED** |
| **Trivial Container Execution** | `docker run --rm hello-world` | Successfully pulled image, created container, streamed output (`Hello from Docker!`), and cleaned up container. | **PASSED** |
| **Available Disk Space** | `Get-Volume -DriveLetter C` | **20.80 GB Free** on Drive `C:\` (275.06 GB total capacity). | **RECORDED** |

---

## 7. Open Decisions & Escalations

1. **PyTorch CUDA Acceleration (Action Required):**
   - *Finding:* System possesses an NVIDIA RTX 4050 GPU (6 GB VRAM), but the currently installed PyTorch package is `2.10.0+cpu`.
   - *Recommendation:* Install CUDA-enabled PyTorch (`torch` compiled for CUDA 12.1/12.4) to leverage hardware acceleration during local model inference.

2. **Docker Desktop Service Startup:**
   - *Status:* **RESOLVED & VERIFIED.** Docker Desktop daemon is running and trivial container execution (`hello-world`) succeeded.

3. **Tesseract Executable Pathing:**
   - *Finding:* Tesseract binary is present at `C:\Program Files\Tesseract-OCR\tesseract.exe`, but not in system `PATH`.
   - *Recommendation:* Add `C:\Program Files\Tesseract-OCR` to system `PATH` or set `pytesseract.pytesseract.tesseract_cmd` explicitly in FastAPI AI configuration.

4. **Model Substitution Policy Compliance:**
   - *Status:* **NO APPROVED MODELS WERE SUBSTITUTED.** Hardware specs (6 GB GPU VRAM, 16 GB RAM) are recorded without altering any model specifications established in PRD v2.3. Realistic model execution benchmarks will be performed in phase `AI-FEASIBILITY-01`.

