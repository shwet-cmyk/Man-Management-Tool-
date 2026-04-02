from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/users", tags=["Users & Roles"])
_USERS: dict[int, dict] = {}


class EmployeeGroup(str, Enum):
    management = "Management"
    operations = "Operations"
    implementation = "Implementation"
    support = "Support"
    development = "Development"
    accounts = "Accounts"


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    employee_group: EmployeeGroup
    reporting_to: int | None = None
    approval_required: bool = True


@router.get("")
def list_users():
    return list(_USERS.values())


@router.post("")
def create_user(payload: UserCreateRequest):
    if any(u["email"] == str(payload.email) for u in _USERS.values()):
        raise HTTPException(status_code=409, detail="Duplicate email")
    if payload.reporting_to is not None and payload.reporting_to == len(_USERS) + 1:
        raise HTTPException(status_code=422, detail="Self reporting is not allowed")
    user_id = len(_USERS) + 1
    data = {"user_id": user_id, **payload.model_dump()}
    _USERS[user_id] = data
    return data
