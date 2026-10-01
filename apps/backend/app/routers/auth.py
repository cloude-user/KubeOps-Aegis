import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["User Authentication"])

# Mock User Store
USER_DB = {}


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
async def register(request: RegisterRequest):
    if request.email in USER_DB:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "email": request.email,
        "password": request.password,
        "full_name": request.full_name,
        "role": "customer",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    USER_DB[request.email] = user_data
    return UserResponse(id=user_id, email=request.email, full_name=request.full_name)


@router.post("/login")
async def login(request: LoginRequest):
    user = USER_DB.get(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "access_token": f"bearer-token-{user['id']}",
        "token_type": "bearer",
        "user": UserResponse(id=user["id"], email=user["email"], full_name=user["full_name"])
    }
