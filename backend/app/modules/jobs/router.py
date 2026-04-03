from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.tasks.router import JOBS, TASKS, _log

router = APIRouter(prefix="/jobs", tags=["Job Management"])


class JobCreateRequest(BaseModel):
    job_name: str
    parent_task: int
    assignee: str
    planned_hours: float | None = Field(default=None, ge=0)
    planned_start: datetime | None = None
    planned_end: datetime | None = None


class JobUpdateRequest(BaseModel):
    job_name: str | None = None
    assignee: str | None = None
    planned_hours: float | None = Field(default=None, ge=0)
    planned_start: datetime | None = None
    planned_end: datetime | None = None


@router.get("/list")
def list_jobs(task_id: int | None = None, assignee: str | None = None, status: str | None = None):
    rows = list(JOBS.values())
    if task_id is not None:
        rows = [r for r in rows if r["task_id"] == task_id]
    if assignee:
        rows = [r for r in rows if r["employee"] == assignee]
    if status:
        rows = [r for r in rows if r["status"] == status]
    return {"count": len(rows), "items": rows}


@router.post("/create")
def create_job(payload: JobCreateRequest):
    task = TASKS.get(payload.parent_task)
    if not task:
        raise HTTPException(status_code=404, detail="Parent task not found")
    if task["status"] in {"CLOSED", "COMPLETED"}:
        raise HTTPException(status_code=422, detail="Job creation blocked if parent task closed")
    jid = len(JOBS) + 1
    JOBS[jid] = {
        "job_id": jid,
        "task_id": payload.parent_task,
        "job_name": payload.job_name,
        "employee": payload.assignee,
        "hourly_rate": 0,
        "start_date": payload.planned_start.date() if payload.planned_start else task["start_date"],
        "due_date": payload.planned_end.date() if payload.planned_end else task["due_date"],
        "status": "NEW",
        "planned_hours": payload.planned_hours,
        "actual_hours": 0.0,
        "actual_cost": 0.0,
        "timesheet_count": 0,
        "created_at": datetime.utcnow(),
    }
    _log("JOB_CREATED", {"job_id": jid, "task_id": payload.parent_task})
    return JOBS[jid]


@router.put("/update/{job_id}")
def update_job(job_id: int, payload: JobUpdateRequest):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    updates = payload.model_dump(exclude_none=True)
    if payload.planned_start and payload.planned_end and payload.planned_end <= payload.planned_start:
        raise HTTPException(status_code=422, detail="End > start if both entered")
    if "assignee" in updates:
        job["employee"] = updates.pop("assignee")
    job.update(updates)
    _log("JOB_UPDATED", {"job_id": job_id})
    return job


def _status(job_id: int, to_status: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job["status"] = to_status
    _log("JOB_STATUS_CHANGED", {"job_id": job_id, "status": to_status})
    return job


@router.post("/start/{job_id}")
def start_job(job_id: int):
    return _status(job_id, "IN_PROGRESS")


@router.post("/pause/{job_id}")
def pause_job(job_id: int):
    return _status(job_id, "PAUSED")


@router.post("/resume/{job_id}")
def resume_job(job_id: int):
    return _status(job_id, "IN_PROGRESS")


@router.post("/complete/{job_id}")
def complete_job(job_id: int):
    return _status(job_id, "COMPLETED")


@router.post("/close/{job_id}")
def close_job(job_id: int):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("timesheet_count", 0) == 0:
        raise HTTPException(status_code=422, detail="Closure blocked if mandatory logs missing")
    return _status(job_id, "CLOSED")


@router.post("/status/{job_id}")
def set_job_status(job_id: int, status: str):
    return _status(job_id, status)
