# ============================================================
# KubeOps-Aegis: Production Multi-Stage Dockerfile
# Autonomous SRE AI Agent Engine for Azure AKS
# ============================================================

# Stage 1: Build & Dependencies Builder
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY agent/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# Stage 2: Minimal Production Runtime
FROM python:3.11-slim AS final

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code & web static assets
COPY agent /app/agent
COPY web /app/web

# Non-root unprivileged security user
RUN useradd -u 10001 -m aegisuser && chown -R aegisuser:aegisuser /app
USER aegisuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["python", "-m", "agent.app.main"]
