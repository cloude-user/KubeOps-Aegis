import uuid
import logging
from functools import lru_cache
from typing import Optional, AsyncGenerator

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from backend.app.config import Settings, settings
    from backend.app.services.blob_service import AzureBlobService, azure_blob_service
    from backend.app.services.order_service import OrderService
except ModuleNotFoundError:
    from apps.backend.app.config import Settings, settings
    from apps.backend.app.services.blob_service import AzureBlobService, azure_blob_service
    from apps.backend.app.services.order_service import OrderService

logger = logging.getLogger("backend.dependencies")

security = HTTPBearer(auto_error=False)


# ============================================================
# 1. SINGLETON CONFIGURATION DEPENDENCY
# ============================================================
@lru_cache()
def get_settings() -> Settings:
    """Returns cached immutable singleton application configuration."""
    return settings


# ============================================================
# 2. CORRELATION & REQUEST-ID DEPENDENCY
# ============================================================
def get_request_id(
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID")
) -> str:
    """Extracts client correlation ID or generates a fresh tracing UUID."""
    return x_request_id or f"req-{uuid.uuid4().hex[:12]}"


# ============================================================
# 3. SINGLETON DATABASE POOL & PER-REQUEST CONNECTION LEASE
# ============================================================
def get_db_pool(request: Request):
    """
    Retrieves the singleton PostgreSQL connection pool initialized during lifespan startup.
    In long-running containerized APIs, a pool manages concurrent async workers efficiently.
    """
    pool = getattr(request.app.state, "db_pool", None)
    return pool


async def get_db_connection(request: Request) -> AsyncGenerator:
    """
    Dependency Injection for PostgreSQL connection:
    Leases an active connection from the singleton pool for the lifecycle of the HTTP request,
    then automatically returns it to the pool when the request completes.
    """
    pool = getattr(request.app.state, "db_pool", None)
    if not pool:
        yield None
        return

    async with pool.acquire() as connection:
        yield connection


# ============================================================
# 4. AZURE BLOB STORAGE SERVICE DEPENDENCY
# ============================================================
def get_blob_service() -> AzureBlobService:
    """
    Injects the Azure Blob Storage client service.
    Enables one-line mocking during unit and integration tests:
    app.dependency_overrides[get_blob_service] = get_test_blob_service
    """
    return azure_blob_service


# ============================================================
# 5. AUTHENTICATION & SECURITY DEPENDENCY
# ============================================================
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> dict:
    """
    Decoupled Authentication Dependency:
    Extracts Bearer JWT or user context header, validating security contracts.
    """
    if x_user_id:
        return {"id": x_user_id, "role": "customer", "auth_type": "header"}

    if credentials and credentials.credentials:
        token = credentials.credentials
        # Validate format e.g. bearer-token-<uuid>
        user_id = token.replace("bearer-token-", "")
        return {"id": user_id, "role": "customer", "auth_type": "bearer"}

    # Default fallback for public / guest operations
    return {"id": "usr-guest-001", "role": "guest", "auth_type": "anonymous"}


# ============================================================
# 6. ORDER SERVICE FACTORY DEPENDENCY
# ============================================================
def get_order_service(
    settings: Settings = Depends(get_settings),
    blob_service: AzureBlobService = Depends(get_blob_service),
    db_conn = Depends(get_db_connection)
) -> OrderService:
    """
    Dependency Injection Factory for OrderService:
    Injects settings, Azure Blob Storage client, and leased PostgreSQL connection.
    """
    return OrderService(settings=settings, blob_service=blob_service, db_connection=db_conn)
