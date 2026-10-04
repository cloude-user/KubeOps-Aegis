import uuid
import hashlib
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

try:
    from backend.app.dependencies import get_db_connection, get_request_id
except ModuleNotFoundError:
    from apps.backend.app.dependencies import get_db_connection, get_request_id

logger = logging.getLogger("backend.routers.auth")

router = APIRouter(prefix="/auth", tags=["User Authentication"])

# Resilient In-Memory Fallback User Store
USER_DB = {}


def hash_password(password: str) -> str:
    """Computes SHA-256 hash of password for secure storage."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "customer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    req: Request,
    db=Depends(get_db_connection),
    request_id: str = Depends(get_request_id)
):
    """
    Registers a new customer.
    Persists user credentials and hashed passwords to the Azure PostgreSQL 'users' table
    using pure parameterized SQL, with resilient fallback to memory.
    """
    client_ip = req.client.host if req.client else "unknown"
    logger.info("[%s] AUDIT_AUTH: Registration attempt for email='%s' (IP=%s)", request_id, request.email, client_ip)

    pwd_hash = hash_password(request.password)
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # 1. Primary: Azure PostgreSQL Persistence
    if db:
        try:
            # Check if user already exists
            existing = await db.fetchrow("SELECT id FROM users WHERE email = $1", request.email)
            if existing:
                logger.warning("[%s] AUDIT_AUTH: Registration rejected - Email '%s' already exists in DB", request_id, request.email)
                raise HTTPException(status_code=400, detail="User with this email already exists.")

            await db.execute(
                """
                INSERT INTO users (id, email, password_hash, full_name, role, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                uuid.UUID(user_id),
                request.email,
                pwd_hash,
                request.full_name,
                "customer",
                now
            )
            logger.info("[%s] AUDIT_AUTH: User '%s' persisted to Azure PostgreSQL table 'users' (ID=%s)", request_id, request.email, user_id)
            return UserResponse(id=user_id, email=request.email, full_name=request.full_name)
        except HTTPException:
            raise
        except Exception as db_err:
            logger.warning("[%s] AUDIT_AUTH: DB write error (%s). Falling back to in-memory store.", request_id, db_err)

    # 2. Resilient Fallback Store
    if request.email in USER_DB:
        logger.warning("[%s] AUDIT_AUTH: Registration rejected (fallback store) - Email '%s' exists", request_id, request.email)
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    user_data = {
        "id": user_id,
        "email": request.email,
        "password_hash": pwd_hash,
        "full_name": request.full_name,
        "role": "customer",
        "created_at": now.isoformat()
    }
    USER_DB[request.email] = user_data

    logger.info("[%s] AUDIT_AUTH: User registered in fallback store with ID=%s", request_id, user_id)
    return UserResponse(id=user_id, email=request.email, full_name=request.full_name)


@router.post("/login")
async def login(
    request: LoginRequest,
    req: Request,
    db=Depends(get_db_connection),
    request_id: str = Depends(get_request_id)
):
    """
    Authenticates user against Azure PostgreSQL 'users' table using pure SQL.
    Verifies password hash and issues a bearer access token.
    """
    client_ip = req.client.host if req.client else "unknown"
    logger.info("[%s] AUDIT_AUTH: Login attempt for email='%s' (IP=%s)", request_id, request.email, client_ip)

    pwd_hash = hash_password(request.password)

    # 1. Primary: Azure PostgreSQL Lookup
    if db:
        try:
            row = await db.fetchrow(
                "SELECT id::text, email, password_hash, full_name, role FROM users WHERE email = $1",
                request.email
            )
            if row:
                if row["password_hash"] != pwd_hash:
                    logger.warning("[%s] AUDIT_AUTH: Password mismatch for email='%s'", request_id, request.email)
                    raise HTTPException(status_code=401, detail="Invalid email or password.")

                user_id = row["id"]
                logger.info("[%s] AUDIT_AUTH: Azure PostgreSQL authentication successful for user ID=%s", request_id, user_id)
                return {
                    "access_token": f"bearer-token-{user_id}",
                    "token_type": "bearer",
                    "user": UserResponse(id=user_id, email=row["email"], full_name=row["full_name"], role=row["role"])
                }
            else:
                logger.warning("[%s] AUDIT_AUTH: User email '%s' not found in Azure PostgreSQL", request_id, request.email)
                raise HTTPException(status_code=401, detail="Invalid email or password.")
        except HTTPException:
            raise
        except Exception as db_err:
            logger.warning("[%s] AUDIT_AUTH: DB lookup failed (%s). Checking fallback store.", request_id, db_err)

    # 2. Resilient Fallback Lookup
    user = USER_DB.get(request.email)
    if not user or user["password_hash"] != pwd_hash:
        logger.warning("[%s] AUDIT_AUTH: Fallback auth failed for email='%s'", request_id, request.email)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    logger.info("[%s] AUDIT_AUTH: Fallback authentication successful for user ID=%s", request_id, user["id"])
    return {
        "access_token": f"bearer-token-{user['id']}",
        "token_type": "bearer",
        "user": UserResponse(id=user["id"], email=user["email"], full_name=user["full_name"], role=user.get("role", "customer"))
    }
