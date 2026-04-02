from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/mobile", tags=["Mobile App Layer"])


class DeviceBindRequest(BaseModel):
    user_id: int
    device_id: str
    method: str = "PIN"


DEVICE_BINDINGS: dict[str, dict] = {}


@router.post("/security/bind-device")
def bind_device(payload: DeviceBindRequest):
    DEVICE_BINDINGS[payload.device_id] = payload.model_dump()
    return {"status": "BOUND", **payload.model_dump()}


@router.get("/home")
def mobile_home(user_id: int):
    return {
        "user_id": user_id,
        "tasks_due_today": 0,
        "notification_summary": {"high": 0, "medium": 0, "low": 0},
        "calendar_day_view": [],
        "gamification_widget": {"points": 0, "streak_days": 0},
    }


@router.get("/offline/bootstrap")
def offline_bootstrap(user_id: int):
    return {
        "user_id": user_id,
        "sync_version": 1,
        "cache": {
            "tasks": [],
            "approvals": [],
            "notifications": [],
            "chat_threads": [],
        },
    }
