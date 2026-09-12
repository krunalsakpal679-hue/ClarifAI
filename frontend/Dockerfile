# ==============================================================================
# ClarifAI Frontend Dockerfile (/frontend/Dockerfile)
# Multi-stage production build (Node.js Build -> Lightweight Nginx Static Server)
# Stack: React + Vite + TypeScript + Tailwind CSS + Zustand + Axios
# Architecture: Static SPA serving with zero embedded secrets
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Installation & Application Build
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Safe build-time environment arguments (never hardcoded secrets)
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Copy dependency manifests first for effective layer caching
COPY package.json package-lock.json* ./

# Clean installation of dependencies
RUN npm install

# Copy source code and configuration files
COPY . .

# Compile TypeScript and generate production static assets into /app/dist
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Lightweight Static Serving
# ------------------------------------------------------------------------------
FROM nginx:alpine AS runner

# Remove default Nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy custom Nginx configuration with SPA routing support
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled production artifacts from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose standard HTTP container port
EXPOSE 80

# Health check to verify static web server availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ || exit 1

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
