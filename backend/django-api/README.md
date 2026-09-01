# ClarifAI — Django Core Backend API Service (`/backend/django-api`)

The Core Backend API Service handles user authentication, document lifecycle management, background task orchestrations (via Celery & Redis), reporting (PDF generation via ReportLab), audit trail logging, and public REST API endpoints.

---

## 1. Quick Start & Local Development

### Prerequisites
- Python 3.13+
- PostgreSQL 15+ (or SQLite for local dev)
- Redis 7+

### Environment Setup
```bash
cd backend/django-api
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### Database Migration & Superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Running the API Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Running Background Celery Worker
```bash
celery -A config worker --loglevel=info
```

---

## 2. Docker & Containerized Environment

### Fresh Docker Build
```bash
docker build --no-cache -t clarifai-django-api .
```

### Running Containerized Stack
```bash
# Web API Container
docker run -d \
  --name clarifai_django_api \
  -p 8000:8000 \
  -e SECRET_KEY="your-production-secret-key" \
  -e DEBUG="True" \
  -e CELERY_BROKER_URL="redis://redis:6379/0" \
  clarifai-django-api

# Celery Worker Container
docker run -d \
  --name clarifai_celery_worker \
  -e SECRET_KEY="your-production-secret-key" \
  -e CELERY_BROKER_URL="redis://redis:6379/0" \
  clarifai-django-api celery -A config worker --loglevel=info
```

### Health Check Endpoint
```bash
curl http://localhost:8000/api/health/
# Response: {"status": "healthy", "service": "ClarifAI Django API", "version": "1.0.0"}
```

---

## 3. Testing & Security Verification

### Running the Full Test Suite Inside Container
```bash
docker run --rm clarifai-django-api python manage.py test --settings=config.settings.test
```

### Dependency Vulnerability & Secret Scanning
```bash
# Audit dependencies against known advisories
python -m pip_audit -r requirements.txt

# Scan repository history for committed secrets
git log -p -S "SECRET_KEY" -S "JWT_SECRET_KEY"
```

---

## 4. Key API Endpoints Overview

- **Auth**: `/api/auth/signup`, `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`
- **Documents**: `/api/documents/`, `/api/documents/{id}/`, `/api/documents/{id}/summary/`, `/api/documents/{id}/clauses/`
- **Chatbot RAG**: `/api/documents/{id}/chat/sessions/`, `/api/documents/{id}/chat/messages/`
- **Comparisons**: `/api/comparisons/`, `/api/comparisons/{id}/`
- **Reports**: `/api/documents/{id}/report/`, `/api/comparisons/{id}/report/`, `/api/reports/{id}/download/`
- **Dashboard**: `/api/dashboard/summary`
