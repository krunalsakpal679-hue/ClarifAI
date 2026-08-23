# ==============================================================================
# ClarifAI AI Microservice Dockerfile (/backend/fastapi-ai)
# Internal AI processing engine (FastAPI + Uvicorn + PyTorch + Tesseract)
# Architecture: Internal-only microservice (invoked strictly by Django REST API)
# ==============================================================================

FROM python:3.11-slim

# Document Model-Loading Strategy:
# Model weights (Legal-BERT, BART-base, Multilingual-E5, IndicTrans2) are NOT baked
# into this image layer to keep image builds lightweight and secure. Models are downloaded
# dynamically at container startup / runtime, or loaded from a mounted host volume (HF_HOME).

# Enforce unbuffered Python stdout/stderr and prevent .pyc generation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HF_HOME=/tmp/huggingface \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

WORKDIR /app

# Install system-level Tesseract OCR engine, language data, and build utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app ./app

# Expose internal microservice port (internal container network only)
EXPOSE 8000

# Health check configuration (internal endpoint query)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Container default entrypoint (FastAPI via Uvicorn)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
