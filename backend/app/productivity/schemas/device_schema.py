from __future__ import annotations
from pydantic import BaseModel

class DeviceRegisterRequest(BaseModel):
    device_uuid: str
    device_name: str
    device_type: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    user_id: int
    company_id: int = 1
    branch_id: int | None = None
    department_id: int | None = None
    agent_version: str | None = None

class DeviceResponse(BaseModel):
    device_id: int
    device_uuid: str
    device_name: str
    registration_status: str
    user_id: int

class DeviceDeactivateResponse(BaseModel):
    success: bool
    device_id: int
