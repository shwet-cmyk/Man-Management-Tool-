from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGO = "HS256"
JWT_TTL_MIN = int(os.getenv("JWT_TTL_MIN", "120"))


def create_access_token(user: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_TTL_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
