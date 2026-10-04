import time
import uuid
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

try:
    from backend.app.config import settings
    from backend.app.routers.auth import router as auth_router
    from backend.app.routers.products import router as products_router
    from backend.app.routers.orders import router as orders_router
    from backend.app.routers.uploads import router as uploads_router
    from backend.app.routers.chaos import router as chaos_router
except ModuleNotFoundError:
    from apps.backend.app.config import settings
    from apps.backend.app.routers.auth import router as auth_router
    from apps.backend.app.routers.products import router as products_router
    from apps.backend.app.routers.orders import router as orders_router
    from apps.backend.app.routers.uploads import router as uploads_router
    from apps.backend.app.routers.chaos import router as chaos_router

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("backend.main")

# ============================================================
# PROMETHEUS METRIC DEFINITIONS (RED METHOD)
# ============================================================
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests processed",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request processing latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUESTS_IN_FLIGHT = Gauge(
    "http_requests_in_flight",
    "Current number of concurrent in-flight HTTP requests"
)

# ============================================================
# APPLICATION LIFECYCLE & SINGLETON DATABASE POOL
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages long-running application lifecycle:
    Initializes a Singleton PostgreSQL Connection Pool on startup and closes it on shutdown.
    Unlike serverless AWS Lambda, containerized APIs use a pooled connection model.
    """
    logger.info("Initializing %s in [%s] environment", settings.APP_NAME, settings.ENVIRONMENT)
    app.state.db_pool = None
    app.state.db_connected = False

    # Initialize Singleton asyncpg connection pool with resilient fallback
    try:
        import asyncpg
        pool = await asyncio.wait_for(
            asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=15.0
            ),
            timeout=4.0
        )
        app.state.db_pool = pool
        app.state.db_connected = True
        logger.info("Successfully initialized Singleton Connection Pool for Azure PostgreSQL (min=2, max=10)")
    except Exception as e:
        logger.warning(
            "PostgreSQL direct pool initialization skipped: %s (Application running in resilient fallback mode)",
            e
        )

    yield

    # Clean graceful shutdown
    if getattr(app.state, "db_pool", None):
        await app.state.db_pool.close()
        logger.info("Closed Azure PostgreSQL connection pool")
    logger.info("Shutting down %s gracefully", settings.APP_NAME)

# ============================================================
# FASTAPI APPLICATION INSTANTIATION (IoC ROOT)
# ============================================================
app = FastAPI(
    title=settings.APP_NAME,
    description="Production 3-Tier Enterprise E-Commerce API with Azure Managed PostgreSQL & Blob Storage Integration",
    version="2.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MIDDLEWARE 1: REQUEST TRACING & STRUCTURED CORRELATION LOGGING
# ============================================================
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """
    Cross-cutting HTTP Concerns:
    - Extracts/assigns unique correlation ID (`X-Request-ID`)
    - Tracks per-request wall-clock execution time
    - Emits structured start and completion logs for Azure Log Analytics
    """
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    client_ip = request.client.host if request.client else "unknown"

    # Skip verbose request logging on Prometheus scrape and Kubernetes probes
    is_probe = request.url.path in ("/metrics", "/healthz")
    if not is_probe:
        logger.info("[%s] HTTP %s %s started (Client=%s)", request_id, request.method, request.url.path, client_ip)

    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        if not is_probe:
            logger.info(
                "[%s] HTTP %s %s completed with status=%d in %sms",
                request_id, request.method, request.url.path, response.status_code, duration_ms
            )
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error("[%s] HTTP %s %s failed after %sms: %s", request_id, request.method, request.url.path, duration_ms, exc)
        raise exc

# ============================================================
# MIDDLEWARE 2: PROMETHEUS TELEMETRY RECORDING
# ============================================================
@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    """Records RED Method metrics for every processed route."""
    if request.url.path in ("/metrics", "/healthz"):
        return await call_next(request)

    method = request.method
    endpoint = request.url.path
    HTTP_REQUESTS_IN_FLIGHT.inc()
    start_time = time.time()
    status_code = "500"

    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    except Exception as exc:
        status_code = "500"
        raise exc
    finally:
        duration = time.time() - start_time
        HTTP_REQUESTS_IN_FLIGHT.dec()
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)

# ============================================================
# GLOBAL EXCEPTION HANDLER
# ============================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "req-unknown")
    logger.error("[%s] Unhandled Exception at %s %s: %s", request_id, request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Please contact the administrator.",
            "request_id": request_id,
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        headers={"X-Request-ID": request_id}
    )

# ============================================================
# HEALTH & METRICS PROBES
# ============================================================
@app.get("/healthz", tags=["Health"])
async def health_check():
    """Kubernetes Liveness and Readiness Probe Endpoint."""
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "CONNECTED" if getattr(app.state, "db_connected", False) else "FALLBACK",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/metrics", tags=["Telemetry"])
async def metrics():
    """Prometheus Scrape Endpoint returning OpenMetrics exposition format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ============================================================
# MOUNT FEATURE ROUTERS
# ============================================================
app.include_router(auth_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(chaos_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
