from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/task-master", tags=["Task Master + Task Group"])


class TaskGroupRequest(BaseModel):
    group_name: str
    description: str | None = None


class TaskMasterRequest(BaseModel):
    task_name: str
    task_group_id: int
    standard_hours: float = Field(..., gt=0)
    minimum_hours: float | None = Field(default=None, ge=0)
    maximum_hours: float | None = Field(default=None, ge=0)
    active: bool = True


TASK_GROUPS: dict[int, dict] = {
    1: {"task_group_id": 1, "group_name": "Implementation", "description": "Implementation execution tasks"},
    2: {"task_group_id": 2, "group_name": "Support", "description": "Support and ticket resolution"},
    3: {"task_group_id": 3, "group_name": "Development", "description": "Development work"},
    4: {"task_group_id": 4, "group_name": "Training", "description": "Training and enablement"},
}
TASK_MASTER: dict[int, dict] = {
    1: {
        "task_master_id": 1,
        "task_name": "Standard Support Ticket Resolution",
        "task_group_id": 2,
        "standard_hours": 2.0,
        "minimum_hours": 1.0,
        "maximum_hours": 4.0,
        "historical_average": 2.0,
        "active": True,
        "executions": 0,
        "updated_at": datetime.utcnow(),
    }
}


def get_task_master(task_master_id: int) -> dict:
    task = TASK_MASTER.get(task_master_id)
    if not task or not task["active"]:
        raise HTTPException(status_code=422, detail="Task must map to an active Task Master record")
    return task


def update_task_master_learning(task_master_id: int, actual_hours: float):
    task = get_task_master(task_master_id)
    task["executions"] += 1
    executions = task["executions"]
    previous_avg = task["historical_average"]
    task["historical_average"] = round(((previous_avg * (executions - 1)) + actual_hours) / executions, 2)

    if actual_hours < task["standard_hours"]:
        task["standard_hours"] = round(actual_hours, 2)

    task["updated_at"] = datetime.utcnow()


@router.get("/groups")
def list_task_groups():
    return list(TASK_GROUPS.values())


@router.post("/groups")
def create_task_group(payload: TaskGroupRequest):
    next_id = len(TASK_GROUPS) + 1
    row = {"task_group_id": next_id, **payload.model_dump()}
    TASK_GROUPS[next_id] = row
    return row


@router.get("")
def list_task_master(task_group_id: int | None = None, active: bool | None = None):
    rows = list(TASK_MASTER.values())
    if task_group_id is not None:
        rows = [r for r in rows if r["task_group_id"] == task_group_id]
    if active is not None:
        rows = [r for r in rows if r["active"] == active]
    return rows


@router.post("")
def create_task_master(payload: TaskMasterRequest):
    if payload.task_group_id not in TASK_GROUPS:
        raise HTTPException(status_code=422, detail="Invalid task group")
    next_id = len(TASK_MASTER) + 1
    row = {
        "task_master_id": next_id,
        **payload.model_dump(),
        "historical_average": payload.standard_hours,
        "executions": 0,
        "updated_at": datetime.utcnow(),
    }
    TASK_MASTER[next_id] = row
    return row


@router.put("/{task_master_id}")
def update_task_master(task_master_id: int, payload: TaskMasterRequest):
    row = TASK_MASTER.get(task_master_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task master not found")
    row.update(payload.model_dump())
    row["updated_at"] = datetime.utcnow()
    return row
