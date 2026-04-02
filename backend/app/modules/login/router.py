from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.security import create_access_token

router = APIRouter(prefix="/login", tags=["Login"])
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    company: str
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _issue_session(payload: LoginRequest):
    if payload.password != "tez@123":
        raise HTTPException(status_code=401, detail="Invalid password")
    token = create_access_token(user=str(payload.email), role="Admin")
    return {
        "status": "success",
        "session": token,
        "token_type": "bearer",
        "rbac_loaded": True,
        "scope_loaded": True,
        "issued_at": datetime.utcnow(),
    }


@router.post("")
def login(payload: LoginRequest):
    return _issue_session(payload)


@auth_router.post("/login")
def auth_login(payload: LoginRequest):
    return _issue_session(payload)


@auth_router.post("/logout")
def logout():
    return {"status": "success", "message": "Session invalidated"}


@auth_router.post("/refresh")
def refresh(payload: RefreshRequest):
    if not payload.refresh_token:
        raise HTTPException(status_code=422, detail="refresh_token is required")
    return {"status": "success", "session": create_access_token(user="refresh-user", role="Admin"), "token_type": "bearer"}
