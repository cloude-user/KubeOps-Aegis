import logging
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from apps.backend.app.config import settings
from apps.backend.app.routers.auth import router as auth_router
from apps.backend.app.routers.products import router as products_router
from apps.backend.app.routers.orders import router as orders_router
from apps.backend.app.routers.uploads import router as uploads_router
from apps.backend.app.routers.chaos import router as chaos_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("backend.main")

app = FastAPI(
    title=settings.APP_NAME,
    description="Production 3-Tier Enterprise E-Commerce API with Azure Managed PostgreSQL & Blob Storage Integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health & Metrics Probes
@app.get("/healthz", tags=["Health"])
async def health_check():
    return {"status": "HEALTHY", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}


@app.get("/metrics", tags=["Telemetry"])
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Mount Feature Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(chaos_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
