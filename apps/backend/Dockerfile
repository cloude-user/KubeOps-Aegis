FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY apps/backend/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim AS final

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/apps/backend \
    PORT=8000

COPY --from=builder /install /usr/local
COPY apps/backend /app/apps/backend
COPY apps/backend/app /app/backend/app

RUN useradd -u 10002 -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

ENTRYPOINT ["uvicorn", "backend.app.main:app", \
            "--host", "0.0.0.0", \
            "--port", "8000", \
            "--timeout-keep-alive", "75", \
            "--timeout-graceful-shutdown", "30", \
            "--limit-concurrency", "200", \
            "--backlog", "2048", \
            "--access-log"]
