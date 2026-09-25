# ClarifAI — AI-Powered Legal Document Simplification & Risk Analysis Engine

ClarifAI is an intelligent legal contract analysis platform designed to transform complex legal documents into plain-language summaries, classify clause-level risks, detect predatory terms, enable grounded RAG chatbot Q&A, compare document versions, and provide English/Hindi translations.

---

## Repository Structure

```text
ClarifAI/
├── backend/
│   ├── fastapi-ai/             # AI Pipeline Microservice (FastAPI + PyTorch + Tesseract + Groq)
│   │   ├── app/                # Application source code (routers, services, models)
│   │   ├── tests/              # Unit & End-to-End Evaluation Test Suite (182 tests)
│   │   ├── docs/               # Service audit reports & specifications
│   │   ├── Dockerfile          # Microservice container definition
│   │   └── README.md           # FastAPI AI Service Living Documentation & Architecture
│   └── django-api/             # Core Backend API Service (Django REST Framework)
├── frontend/                   # Frontend SPA (React 18 + Vite + TypeScript + Tailwind + Zustand + Axios)
│   ├── src/                    # UI Components, state, and test suites
│   ├── Dockerfile              # Multi-stage production container definition
│   ├── nginx.conf              # SPA static web server configuration
│   └── package.json            # Dependencies & scripts
├── docs/                       # Project Documentation & Audit Reports
│   ├── frontend-docker-setup.md
│   ├── ai-environment-report.md
│   ├── ai-model-inventory.md
│   ├── ai-feasibility-report.md
│   ├── ai-output-schemas.md
│   ├── ai-failure-matrix.md
│   ├── ai-evaluation-report.md
│   ├── ai-docker-validation-report.md
│   └── ai-final-validation-report.md
└── README.md                   # Root Project Repository Overview
```

---

## AI Microservice (`/backend/fastapi-ai`)

The AI Pipeline microservice is fully implemented, verified with **182 passing unit tests**, and documented in detail in [`/backend/fastapi-ai/README.md`](./backend/fastapi-ai/README.md).

### Key Features Implemented:
- **PDF Text Extraction & Selective OCR**: PyMuPDF digital extraction with adaptive Tesseract OCR v5 fallback (`eng` + `hin`).
- **Deterministic Text Cleaning & Segmentation**: Rule-based normalization preserving verbatim clause text.
- **8-Category Clause Classification**: Payment, Termination, Renewal, Confidentiality, Liability, IP, Privacy, Dispute Resolution.
- **Stage 1 Rule Engine (R001–R014)**: Deterministic legal risk signal detector.
- **Legal-BERT Risk Classifier**: Contextual 4-severity classifier (High, Moderate, Low, Safe) with why-flagged explanations.
- **Executive Summarization**: BART-base 4-field document summary generator (`purpose`, `obligations`, `key_terms`, `key_risks`).
- **Multilingual-E5 Embeddings & Qdrant Vector Storage**: 768-dimensional dense vectors stored with dual-field ownership isolation (`user_id` + `document_id`).
- **Evidence-Grounded RAG Chatbot**: Double-gated relevance (0.35) and sufficiency checks preventing hallucination.
- **Contract Comparison Engine**: Pairwise embedding similarity classification (`MATCHED`, `CHANGED`, `MISSING`).
- **Multilingual Support**: English to Hindi translation for summaries, simplified clauses, explanations, and chatbot answers.
- **Security & Safety Guardrails**: 12-layer hallucination prevention, prompt-injection leak filtering, and 6 versioned Pydantic output schema validators.

---

## Documentation Quick Links

- ⚛️ [Frontend Docker Setup & Operations](./docs/frontend-docker-setup.md)
- 📖 [FastAPI AI Microservice Living README](./backend/fastapi-ai/README.md)
- 📊 [AI Output Schemas Specification](./docs/ai-output-schemas.md)
- 🛡️ [AI Pipeline Failure-Mode Matrix](./docs/ai-failure-matrix.md)
- 🧪 [AI End-to-End Evaluation Report](./docs/ai-evaluation-report.md)
- 🐳 [AI Microservice Docker Validation Report](./docs/ai-docker-validation-report.md)
- 📋 [AI Pipeline Final Handoff Validation Report](./docs/ai-final-validation-report.md)

---

---

## Quick Start (Docker Compose & Onboarding)

### 1. Environment Setup
Clone the repository and create the local environment file from the template:
```bash
cp .env.example .env
# Option: Add your GROQ_API_KEY to .env for live Groq LLM completions
```

### 2. Launch Full Stack Orchestration
Build container images and start all multi-service containers (`postgres`, `redis`, `qdrant`, `fastapi-ai`, `django-api`, `celery-worker`, `frontend`):
```bash
docker compose up --build -d
```

Service Access Endpoints:
- ⚛️ **Frontend SPA Application**: [http://localhost:5173](http://localhost:5173)
- 🐍 **Django REST API Gateway**: [http://localhost:8000/api/health/](http://localhost:8000/api/health/)
- 🤖 **FastAPI AI Microservice (Internal)**: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Master Test Suite Verification
Run component and integration test suites:
```bash
# 1. Frontend Test Suite (Vitest - 262 tests)
cd frontend && npm run test

# 2. AI Microservice Test Suite (Pytest - 196 tests)
cd backend/fastapi-ai && python -m pytest tests/

# 3. Django Backend & Master E2E Suite (Django Test Runner - 104 tests)
cd backend/django-api && python manage.py test
```

---

## Frontend Application (`/frontend`)

The ClarifAI Frontend is built with React 18, Vite, TypeScript, Tailwind CSS, Zustand, and Axios.

### Mock Service Layer & Production Isolation (PRD Section 11 & Ch. 30.8)

The frontend features a realistic mock service layer under `src/services/mocks/` covering all Section 8 API contracts (Auth, Dashboard, Documents, Chat, Comparisons, Reports).

- **Switching Strategy**: Controlled strictly in `src/services/api/index.ts` via the `VITE_USE_MOCKS` environment variable:
  - **Development & UI Preview**: Defaults to `VITE_USE_MOCKS=true` (`import.meta.env.VITE_USE_MOCKS !== 'false'`), allowing complete offline frontend verification, state testing, and UI demonstration without backend dependencies.
  - **Production & Live Integration**: Configured with `VITE_USE_MOCKS=false`. When set, the application exclusively connects through the production Axios client (`apiClient`) targeting the live API gateway (`VITE_API_BASE_URL`), with silent 401 token refresh, 429 rate-limit handling (`Retry-After`), AI-service-unavailable formatting, and standard `{ error: { code, message } }` parsing.
- **Production Safety**: Mock data stores contain only synthetic contracts with zero baked-in credentials or secrets. Production builds configured with `VITE_USE_MOCKS=false` route exclusively to the real backend.

