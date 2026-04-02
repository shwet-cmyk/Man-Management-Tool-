from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/login", tags=["Login"])


class LoginRequest(BaseModel):
    company: str
    email: EmailStr
    password: str


@router.post("")
def login(payload: LoginRequest):
    if payload.password != "tez@123":
        raise HTTPException(status_code=401, detail="Invalid password")
    return {
        "status": "success",
        "session": "mock-session-token",
        "rbac_loaded": True,
        "scope_loaded": True,
    }
