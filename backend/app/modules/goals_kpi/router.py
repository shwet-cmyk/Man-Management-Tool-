from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.event_bus import publish_event
from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry

router = APIRouter(prefix="/goals", tags=["Goals & KPI Management"])


class GoalType(str, Enum):
    revenue = "REVENUE"
    execution = "EXECUTION"
    sla = "SLA"
    custom = "CUSTOM"


class GoalStatus(str, Enum):
    draft = "DRAFT"
    active = "ACTIVE"
    on_track = "ON_TRACK"
    off_track = "OFF_TRACK"
    completed = "COMPLETED"
    closed = "CLOSED"


class GoalCreateRequest(BaseModel):
    goal_name: str
    description: str | None = None
    goal_type: GoalType
    kpi_metric: str
    target_value: float
    start_date: date
    end_date: date
    owner: str
    linked_projects: list[int] = Field(default_factory=list)
    linked_tasks: list[int] = Field(default_factory=list)


class GoalProgressRequest(BaseModel):
    current_value: float
    actor: str


GOALS: dict[int, dict] = {}


@router.post("")
def create_goal(payload: GoalCreateRequest):
    if payload.start_date > payload.end_date:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date")
    if payload.target_value <= 0:
        raise HTTPException(status_code=422, detail="target_value must be greater than zero")

    goal_id = len(GOALS) + 1
    row = {
        "goal_id": goal_id,
        **payload.model_dump(),
        "current_value": 0.0,
        "achievement_pct": 0.0,
        "status": GoalStatus.draft,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    GOALS[goal_id] = row

    add_audit_entry(
        AuditCreateRequest(
            user_name=payload.owner,
            module="GOAL",
            reference_id=str(goal_id),
            action_type="CREATE",
            new_value={"goal_name": payload.goal_name, "target_value": payload.target_value},
        )
    )
    publish_event("GOAL_CREATED", {"goal_id": goal_id, "owner": payload.owner})
    return row


@router.get("")
def list_goals(status: GoalStatus | None = None):
    rows = list(GOALS.values())
    if status:
        rows = [r for r in rows if r["status"] == status]
    return rows


@router.get("/{goal_id}")
def get_goal(goal_id: int):
    row = GOALS.get(goal_id)
    if not row:
        raise HTTPException(status_code=404, detail="Goal not found")
    return row


@router.patch("/{goal_id}/progress")
def update_goal_progress(goal_id: int, payload: GoalProgressRequest):
    row = GOALS.get(goal_id)
    if not row:
        raise HTTPException(status_code=404, detail="Goal not found")

    old = row["current_value"]
    row["current_value"] = payload.current_value
    row["achievement_pct"] = min(100.0, round((payload.current_value / row["target_value"]) * 100, 2))
    row["status"] = GoalStatus.on_track if row["achievement_pct"] >= 75 else GoalStatus.off_track
    if row["achievement_pct"] >= 100:
        row["status"] = GoalStatus.completed
    row["updated_at"] = datetime.utcnow()

    add_audit_entry(
        AuditCreateRequest(
            user_name=payload.actor,
            module="GOAL",
            reference_id=str(goal_id),
            action_type="PROGRESS_UPDATE",
            field_name="current_value",
            old_value=old,
            new_value=payload.current_value,
        )
    )
    publish_event(
        "GOAL_PROGRESS_UPDATED",
        {"goal_id": goal_id, "achievement_pct": row["achievement_pct"], "status": row["status"]},
    )
    return row


@router.get("/reports/achievement")
def goal_achievement_report():
    rows = list(GOALS.values())
    return {
        "totals": {
            "goals": len(rows),
            "completed": len([r for r in rows if r["status"] == GoalStatus.completed]),
            "off_track": len([r for r in rows if r["status"] == GoalStatus.off_track]),
        },
        "items": rows,
    }
