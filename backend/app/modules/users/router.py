from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.modules.org.router import _BRANCHES, _COMPANIES, _DEPARTMENTS
from app.modules.system_audit.service import audit_service

router = APIRouter(tags=["Users & Roles"])
_USERS: dict[int, dict] = {}
_USER_PROFILE: dict[int, dict] = {}


class EmployeeGroup(str, Enum):
    management = "Management"
    operations = "Operations"
    implementation = "Implementation"
    support = "Support"
    development = "Development"
    accounts = "Accounts"


class PersonaRole(str, Enum):
    super_admin = "SuperAdmin"
    admin = "Admin"
    manager = "Manager"
    user = "User"
    developer = "Developer"


class UserCreateRequest(BaseModel):
    employee_code: str
    full_name: str
    email: EmailStr
    mobile_no: str | None = None
    company_id: int
    branch_id: int
    department_id: int
    role: PersonaRole
    employee_group: EmployeeGroup = EmployeeGroup.operations
    reporting_manager: int | None = None
    designation: str | None = None
    joining_date: str | None = None
    work_shift: str | None = None
    default_dashboard: str | None = None
    bruno_access: bool = False
    productivity_agent_enabled: bool = False
    status: bool = True


class UserUpdateRequest(UserCreateRequest):
    pass


class ProfileUpdateRequest(BaseModel):
    full_name: str
    mobile: str | None = None
    designation: str | None = None
    time_zone: str | None = None
    notification_preferences: list[str] = []
    working_hours_start: str | None = None
    working_hours_end: str | None = None
    language: str | None = None
    dashboard_preference: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def _audit(action: str, reference_id: int, payload: dict) -> None:
    audit_service.add(
        {
            "user_name": "system",
            "module": "USER_MASTER",
            "reference_id": str(reference_id),
            "action_type": action,
            "field_name": "payload",
            "old_value": None,
            "new_value": str(payload),
            "remarks": None,
            "context": payload,
        }
    )


@router.get("/users")
@router.get("/users/list")
def list_users(company_id: int | None = None):
    rows = list(_USERS.values())
    if company_id is not None:
        rows = [r for r in rows if r["company_id"] == company_id]
    return {"count": len(rows), "items": rows}


@router.get("/users/{user_id}")
def get_user(user_id: int):
    row = _USERS.get(user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


@router.post("/users")
@router.post("/users/create")
def create_user(payload: UserCreateRequest):
    if any(u["email"].lower() == str(payload.email).lower() for u in _USERS.values()):
        raise HTTPException(status_code=409, detail="Email duplicate blocks save")
    if payload.company_id not in _COMPANIES:
        raise HTTPException(status_code=422, detail="Company not found")
    branch = _BRANCHES.get(payload.branch_id)
    if not branch or branch["company_id"] != payload.company_id:
        raise HTTPException(status_code=422, detail="Branch/department mismatch blocks save")
    dept = _DEPARTMENTS.get(payload.department_id)
    if not dept or dept["branch_id"] != payload.branch_id:
        raise HTTPException(status_code=422, detail="Department must belong to selected branch")

    user_id = len(_USERS) + 1
    data = {
        "id": user_id,
        **payload.model_dump(),
        "status": "ACTIVE" if payload.status else "INACTIVE",
        "last_login": None,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _USERS[user_id] = data
    _USER_PROFILE[user_id] = {
        "user_id": user_id,
        "full_name": payload.full_name,
        "email": str(payload.email),
        "mobile": payload.mobile_no,
        "designation": payload.designation,
        "time_zone": None,
        "notification_preferences": ["in-app"],
        "working_hours_start": None,
        "working_hours_end": None,
        "language": "en",
        "dashboard_preference": payload.default_dashboard or "dashboard_main",
        "profile_completion_status": "PENDING",
        "password": "tez@123",
    }
    _audit("USER_CREATED", user_id, data)
    return data


@router.put("/users/update/{user_id}")
def update_user(user_id: int, payload: UserUpdateRequest):
    row = _USERS.get(user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    row.update(payload.model_dump())
    row["status"] = "ACTIVE" if payload.status else "INACTIVE"
    _audit("USER_UPDATED", user_id, row)
    return row


@router.post("/users/deactivate/{user_id}")
def deactivate_user(user_id: int):
    row = _USERS.get(user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    row["status"] = "INACTIVE"
    _audit("USER_DEACTIVATED", user_id, row)
    return {"status": "success", "item": row}


@router.post("/users/reset-password/{user_id}")
def reset_password(user_id: int):
    profile = _USER_PROFILE.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    profile["password"] = "tez@123"
    _audit("USER_PASSWORD_RESET", user_id, {"password_reset": True})
    return {"status": "success", "message": "Password reset to temporary value"}


@router.post("/users/unlock/{user_id}")
def unlock_user(user_id: int):
    row = _USERS.get(user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    row["status"] = "ACTIVE"
    _audit("USER_UNLOCKED", user_id, row)
    return {"status": "success", "item": row}


@router.get("/profile/me")
def profile_me(user_id: int = 1):
    profile = _USER_PROFILE.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profile/update")
def update_profile(payload: ProfileUpdateRequest, user_id: int = 1):
    profile = _USER_PROFILE.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if payload.working_hours_start and payload.working_hours_end and payload.working_hours_end <= payload.working_hours_start:
        raise HTTPException(status_code=422, detail="Working hours end > start is required")

    profile.update(payload.model_dump())
    profile["profile_completion_status"] = "COMPLETE"
    _audit("PROFILE_UPDATED", user_id, payload.model_dump())
    return profile


@router.post("/profile/change-password")
def profile_change_password(payload: ChangePasswordRequest, user_id: int = 1):
    profile = _USER_PROFILE.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if payload.old_password != profile["password"]:
        raise HTTPException(status_code=401, detail="Old password mismatch")
    profile["password"] = payload.new_password
    _audit("PROFILE_PASSWORD_CHANGED", user_id, {"password_changed": True})
    return {"status": "success", "message": "Password changed"}


@router.post("/profile/reset-guided-tour")
def reset_guided_tour(user_id: int = 1):
    profile = _USER_PROFILE.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile["guided_tour_reset_at"] = datetime.now(UTC).isoformat()
    _audit("PROFILE_GUIDED_TOUR_RESET", user_id, {"guided_tour_reset": True})
    return {"status": "success", "message": "Guided tour reset"}


@router.get('/users/reports/summary')
def user_report_summary():
    rows = list(_USERS.values())
    by_role: dict[str, int] = {}
    by_status: dict[str, int] = {"ACTIVE": 0, "INACTIVE": 0}
    for row in rows:
        role = row['role'] if isinstance(row['role'], str) else row['role'].value
        by_role[role] = by_role.get(role, 0) + 1
        by_status[row['status']] = by_status.get(row['status'], 0) + 1
    bruno_enabled = len([u for u in rows if u.get("bruno_access")])
    agent_enabled = len([u for u in rows if u.get("productivity_agent_enabled")])
    return {
        'total_users': len(rows),
        'active_vs_inactive': by_status,
        'by_role': by_role,
        'bruno_adoption_pct': (bruno_enabled / len(rows) * 100) if rows else 0,
        'productivity_agent_coverage_pct': (agent_enabled / len(rows) * 100) if rows else 0,
    }
