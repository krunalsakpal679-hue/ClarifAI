# ClarifAI Frontend (`/frontend`)

The ClarifAI Frontend is a modern Single Page Application (SPA) built with React 18, Vite, TypeScript, Tailwind CSS, Zustand, Framer Motion, and Axios.

---

## 1. Quick Start & Local Development

### Prerequisites
- Node.js 20+
- npm 10+

### Installation
```bash
cd frontend
npm install
```

### Environment Configuration
The frontend uses Vite environment variables separated by mode:

| File | Environment | `VITE_USE_MOCKS` | Purpose |
|---|---|---|---|
| `.env.development` | Development | `true` | Offline UI development using synthetic contracts in `src/services/mocks/` |
| `.env.production` | Production Build | `false` | Real backend integration (`apiClient`) targeting Django REST API |
| `.env.example` | Template | `false` | Example template for custom deployments |

To point local development to a running Django API backend:
```bash
# In frontend/.env.local (gitignored)
VITE_USE_MOCKS=false
VITE_API_BASE_URL=http://localhost:8000
```
Or use the built-in Vite dev server proxy which forwards `/api` requests directly to `http://localhost:8000`.

### Running Development Server
```bash
npm run dev
```

---

## 2. Quality Gates & Testing Scripts

| Command | Purpose |
|---|---|
| `npm test` | Run Vitest suite across all 44 test files (262 tests) |
| `npm run test:integration` | Run end-to-end integration test runner against live Django API |
| `npm run type-check` | Run TypeScript strict compiler checks (`tsc -b --noEmit`) |
| `npm run lint` | Run ESLint across all TypeScript and React source files |
| `npm run build` | Compile optimized production bundle (`dist/`) |
| `npm run preview` | Locally preview production build |

---

## 3. Production Docker Build

Build multi-stage production container image:
```bash
docker build -t clarifai-frontend:latest .
```

Run container:
```bash
docker run -d -p 8080:80 --name clarifai_frontend clarifai-frontend:latest
```

The container runs Nginx serving static SPA assets with strict security headers (`X-Frame-Options`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Referrer-Policy: strict-origin-when-cross-origin`).
