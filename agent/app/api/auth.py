from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from agent.app.core.security import create_access_token, verify_password, get_password_hash
from agent.app.core.config import settings

router = APIRouter(tags=["Authentication"])

# Pre-configured demo SRE Admin user (Can be synced with Azure Entra ID in production)
DEMO_USER_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("AegisSre2026!"),
        "role": "sre-lead"
    }
}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/token", response_model=TokenResponse)
@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = DEMO_USER_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user["username"],
        role=user["role"]
    )
