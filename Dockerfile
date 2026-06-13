# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Build the React frontend
# ──────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Install dependencies first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

COPY frontend/ .

# Build the production bundle (tsc -b && vite build)
RUN npm run build

# Patch the hardcoded dev API base URL so requests use relative paths through nginx.
# This avoids modifying application source code for deployment.
RUN find dist -name "*.js" -exec sed -i 's|http://localhost:8006||g' {} \;


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Production image — Python backend + nginx + built frontend
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Install nginx and supervisor to manage two processes in one container
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx supervisor curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Backend dependencies ──────────────────────────────────────────────────────
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# ── Project source (backend + all service layers) ────────────────────────────
COPY backend/   ./backend/
COPY services/  ./services/
COPY adapters/  ./adapters/
COPY domains/   ./domains/
COPY shared/    ./shared/
COPY mock-data/ ./mock-data/

# ── Frontend built artifacts ──────────────────────────────────────────────────
COPY --from=frontend-builder /build/dist ./frontend/dist

# ── nginx configuration ───────────────────────────────────────────────────────
COPY frontend/nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# ── Supervisor configuration ──────────────────────────────────────────────────
COPY supervisord.conf /etc/supervisor/conf.d/workbench.conf

# ── Startup script ────────────────────────────────────────────────────────────
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Hugging Face Docker Spaces default port
EXPOSE 7860

ENTRYPOINT ["/start.sh"]
