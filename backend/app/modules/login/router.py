from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.security import create_access_token

router = APIRouter(prefix="/login", tags=["Login"])
auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@dataclass
class AuthPolicy:
    max_failed_attempts: int = 3
    lock_minutes: int = 15
    otp_after_failures: int = 2
    password_expiry_days: int = 90


@dataclass
class UserRecord:
    user_id: int
    username: str
    email: str
    password: str
    role: str
    is_active: bool = True
    first_login: bool = False
    failed_attempts: int = 0
    locked_until: datetime | None = None
    otp_code: str | None = None
    otp_expires_at: datetime | None = None
    password_changed_at: datetime = field(default_factory=lambda: datetime.now(UTC) - timedelta(days=40))


POLICY = AuthPolicy()
USERS: dict[str, UserRecord] = {
    "admin@tez.com": UserRecord(user_id=1, username="admin", email="admin@tez.com", password="tez@123", role="Admin", first_login=True),
    "superadmin@tez.com": UserRecord(user_id=2, username="superadmin", email="superadmin@tez.com", password="tez@123", role="SuperAdmin"),
    "manager@tez.com": UserRecord(user_id=3, username="manager", email="manager@tez.com", password="tez@123", role="Manager"),
    "inactive@tez.com": UserRecord(user_id=4, username="inactive", email="inactive@tez.com", password="tez@123", role="User", is_active=False),
}
SESSIONS: dict[str, dict] = {}
PASSWORD_HISTORY: dict[int, list[str]] = {u.user_id: [u.password] for u in USERS.values()}
AUDIT_LOG: list[dict] = []


class LoginRequest(BaseModel):
    company: str | None = None
    identifier: str | None = None
    email: EmailStr | None = None
    password: str
    otp: str | None = None
    captcha_token: str | None = None
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class AuthAnalyticsFilter(BaseModel):
    days: int = 7


def _now() -> datetime:
    return datetime.now(UTC)


def _log(event: str, user: str, status: Literal["SUCCESS", "FAIL"], detail: str) -> None:
    AUDIT_LOG.append(
        {
            "id": str(uuid4()),
            "event": event,
            "user": user,
            "status": status,
            "detail": detail,
            "created_at": _now().isoformat(),
        }
    )


def _find_user(identifier: str | None, email: str | None) -> UserRecord | None:
    if email and email in USERS:
        return USERS[email]
    if not identifier:
        return None
    for row in USERS.values():
        if row.email == identifier or row.username == identifier:
            return row
    return None


def _role_redirect(role: str) -> str:
    return "/control-panel" if role == "SuperAdmin" else "/dashboard"


def _is_password_expired(user: UserRecord) -> bool:
    return (_now() - user.password_changed_at).days >= POLICY.password_expiry_days


def _issue_session(user: UserRecord, remember_me: bool) -> dict:
    ttl = timedelta(days=7 if remember_me else 1)
    access_token = create_access_token(user=str(user.email), role=user.role)
    refresh_token = str(uuid4())
    session = {
        "session_id": str(uuid4()),
        "user_id": user.user_id,
        "role": user.role,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": (_now() + ttl).isoformat(),
    }
    SESSIONS[refresh_token] = session
    return session


def _build_login_response(user: UserRecord, remember_me: bool) -> dict:
    session = _issue_session(user, remember_me)
    first_login_flag = user.first_login
    user.first_login = False
    _log("LOGIN", user.email, "SUCCESS", "Login success")
    return {
        "status": "success",
        "session": session["access_token"],
        "refresh_token": session["refresh_token"],
        "token_type": "bearer",
        "role": user.role,
        "redirect_to": _role_redirect(user.role),
        "first_login": first_login_flag,
        "password_expired": _is_password_expired(user),
        "rbac_loaded": True,
        "scope_loaded": True,
        "issued_at": _now(),
    }


def _check_user_state(user: UserRecord) -> None:
    if not user.is_active:
        _log("LOGIN", user.email, "FAIL", "Inactive account")
        raise HTTPException(status_code=403, detail="Account inactive. Contact admin.")
    if not user.role:
        _log("LOGIN", user.email, "FAIL", "Role missing")
        raise HTTPException(status_code=403, detail="Role not assigned. Contact admin.")
    if user.locked_until and user.locked_until > _now():
        _log("LOGIN", user.email, "FAIL", "Account locked")
        raise HTTPException(status_code=423, detail=f"Account locked until {user.locked_until.isoformat()}")


def _validate_password(user: UserRecord, password: str, captcha_token: str | None) -> None:
    if user.password == password:
        user.failed_attempts = 0
        return

    user.failed_attempts += 1
    captcha_required = user.failed_attempts >= POLICY.otp_after_failures
    if user.failed_attempts >= POLICY.max_failed_attempts:
        user.locked_until = _now() + timedelta(minutes=POLICY.lock_minutes)
        _log("LOGIN_LOCK", user.email, "FAIL", "Too many failed attempts")
        raise HTTPException(status_code=423, detail="Account locked due to failed attempts")
    _log("LOGIN", user.email, "FAIL", "Invalid password")
    if captcha_required and not captcha_token:
        raise HTTPException(status_code=400, detail="CAPTCHA required after repeated failed attempts")
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("")
def login(payload: LoginRequest):
    user = _find_user(payload.identifier, payload.email)
    if not user:
        _log("LOGIN", payload.identifier or str(payload.email), "FAIL", "User not found")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    _check_user_state(user)
    _validate_password(user, payload.password, payload.captcha_token)

    otp_required = user.failed_attempts >= POLICY.otp_after_failures
    if otp_required:
        if payload.otp != "123456":
            user.otp_code = "123456"
            user.otp_expires_at = _now() + timedelta(minutes=5)
            _log("LOGIN_OTP", user.email, "FAIL", "OTP required")
            raise HTTPException(status_code=428, detail="OTP required. Use OTP 123456 for demo.")

    return _build_login_response(user, payload.remember_me)


@auth_router.post("/login")
def auth_login(payload: LoginRequest):
    return login(payload)


@auth_router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    user = USERS.get(str(payload.email))
    if not user:
        return {"status": "success", "message": "If the account exists, a reset OTP has been sent."}
    user.otp_code = "123456"
    user.otp_expires_at = _now() + timedelta(minutes=10)
    _log("FORGOT_PASSWORD", user.email, "SUCCESS", "Reset OTP issued")
    return {"status": "success", "message": "OTP sent", "otp_hint": "Use 123456 for local demo"}


@auth_router.post("/verify-otp")
def verify_otp(payload: VerifyOtpRequest):
    user = USERS.get(str(payload.email))
    if not user or not user.otp_code or not user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP not requested")
    if user.otp_expires_at < _now():
        raise HTTPException(status_code=400, detail="OTP expired")
    if payload.otp != user.otp_code:
        _log("VERIFY_OTP", user.email, "FAIL", "Invalid OTP")
        raise HTTPException(status_code=401, detail="Invalid OTP")
    _log("VERIFY_OTP", user.email, "SUCCESS", "OTP verified")
    return {"status": "success", "message": "OTP verified"}


@auth_router.post("/logout")
def logout(payload: LogoutRequest | None = None):
    refresh_token = payload.refresh_token if payload else None
    if refresh_token and refresh_token in SESSIONS:
        session = SESSIONS.pop(refresh_token)
        _log("LOGOUT", str(session["user_id"]), "SUCCESS", "Session invalidated")
    return {"status": "success", "message": "Session invalidated"}


@auth_router.post("/refresh")
def refresh(payload: RefreshRequest):
    session = SESSIONS.get(payload.refresh_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh_token")
    user = next((u for u in USERS.values() if u.user_id == session["user_id"]), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    next_session = _issue_session(user, remember_me=False)
    _log("REFRESH", user.email, "SUCCESS", "Token refreshed")
    return {
        "status": "success",
        "session": next_session["access_token"],
        "refresh_token": next_session["refresh_token"],
        "token_type": "bearer",
    }


@auth_router.get("/analytics/login-summary")
def login_summary(days: int = 7):
    cutoff = _now() - timedelta(days=days)
    rows = [r for r in AUDIT_LOG if datetime.fromisoformat(r["created_at"]) >= cutoff]
    total_success = len([r for r in rows if r["event"] == "LOGIN" and r["status"] == "SUCCESS"])
    total_fail = len([r for r in rows if r["event"] == "LOGIN" and r["status"] == "FAIL"])
    lockouts = len([r for r in rows if r["event"] == "LOGIN_LOCK"])
    first_login_pending = len([u for u in USERS.values() if u.first_login])
    inactive_users = len([u for u in USERS.values() if not u.is_active])
    failed_attempts = [{"email": u.email, "failed_attempts": u.failed_attempts} for u in USERS.values() if u.failed_attempts > 0]

    daily: dict[str, int] = {}
    for row in rows:
        if row["event"] != "LOGIN" or row["status"] != "SUCCESS":
            continue
        day = row["created_at"][:10]
        daily[day] = daily.get(day, 0) + 1

    return {
        "range_days": days,
        "login_success": total_success,
        "login_failed": total_fail,
        "lockouts": lockouts,
        "inactive_users": inactive_users,
        "first_login_pending": first_login_pending,
        "failed_attempt_report": failed_attempts,
        "daily_logins": [{"date": k, "count": v} for k, v in sorted(daily.items())],
        "lock_report": [r for r in rows if r["event"] == "LOGIN_LOCK"],
    }


@auth_router.get("/audit/login-events")
def login_audit(limit: int = 50):
    return {"count": min(limit, len(AUDIT_LOG)), "items": AUDIT_LOG[-limit:]}
