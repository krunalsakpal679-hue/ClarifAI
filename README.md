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
├── docs/                       # Project Documentation & Audit Reports
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

- 📖 [FastAPI AI Microservice Living README](./backend/fastapi-ai/README.md)
- 📊 [AI Output Schemas Specification](./docs/ai-output-schemas.md)
- 🛡️ [AI Pipeline Failure-Mode Matrix](./docs/ai-failure-matrix.md)
- 🧪 [AI End-to-End Evaluation Report](./docs/ai-evaluation-report.md)
- 🐳 [AI Microservice Docker Validation Report](./docs/ai-docker-validation-report.md)
- 📋 [AI Pipeline Final Handoff Validation Report](./docs/ai-final-validation-report.md)

---

## Running the AI Service Locally

```bash
cd backend/fastapi-ai
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GROQ_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run test suite:
```bash
python -m pytest -v
```
