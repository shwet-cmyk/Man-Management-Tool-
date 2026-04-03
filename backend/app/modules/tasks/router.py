from __future__ import annotations

from datetime import date, datetime, time, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.status_engine.router import ModuleType, PriorityType, validate_status_transition
from app.modules.approval.router import ApprovalModule, ApprovalTriggerRequest, trigger_approval_request
from app.modules.task_master.router import TASK_MASTER, TASK_GROUPS, get_task_master, update_task_master_learning

router = APIRouter(prefix="/tasks", tags=["Task Management Module"])


class DependencyType(str, Enum):
    task = "TASK"
    job = "JOB"


class BillingType(str, Enum):
    fixed = "FIXED"
    derived = "DERIVED"


class TeamMemberRequest(BaseModel):
    employee_name: str
    hourly_rate: float = Field(..., ge=0)


class DependencyRequest(BaseModel):
    dependency_type: DependencyType
    dependency_id: int


class TaskCreateRequest(BaseModel):
    task_master_id: int
    task_name: str | None = None
    project_id: int
    phase_name: str
    description: str | None = None
    priority: PriorityType
    showstopper: bool = False
    start_date: date
    due_date: date
    sla_manual_hours: float | None = Field(default=None, gt=0)
    has_dependency: bool = False
    dependency: DependencyRequest | None = None
    task_owner: str
    team_members: list[TeamMemberRequest] = Field(..., min_length=1)
    estimated_hours: float = Field(..., ge=0)
    estimated_cost: float = Field(..., ge=0)
    billing_type: BillingType = BillingType.derived
    is_billable: bool = True
    billing_amount: float | None = Field(default=None, ge=0)


class TaskUpdateRequest(BaseModel):
    task_name: str | None = None
    description: str | None = None
    priority: PriorityType | None = None
    due_date: date | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    billing_type: BillingType | None = None
    is_billable: bool | None = None
    billing_amount: float | None = Field(default=None, ge=0)


class TaskStatusUpdateRequest(BaseModel):
    status: str
    actor: str
    actor_role: str
    remark: str | None = None
    approval_granted: bool = False


class JobStatusUpdateRequest(BaseModel):
    status: str
    actor: str
    actor_role: str
    remark: str | None = None
    approval_granted: bool = False


class TimesheetCreateRequest(BaseModel):
    job_id: int
    employee: str
    entry_date: date
    start_time: time
    end_time: time
    remarks: str | None = None
    expense: float = Field(default=0, ge=0)
    reimbursement: float = Field(default=0, ge=0)
    attachment: str | None = None
    creator_user_id: int


class BillingFinalizeRequest(BaseModel):
    task_id: int
    creator_user_id: int
    billing_amount: float = Field(..., ge=0)


PERMISSIONS = [
    "Create Task",
    "Edit Task",
    "Delete Task",
    "Assign Task",
    "Assign Job",
    "Change Status",
    "Approve Completion",
    "View Cost",
    "View Timesheet",
    "Export",
    "View Analytics",
]

TASKS: dict[int, dict] = {}
JOBS: dict[int, dict] = {}
TIMESHEETS: dict[int, dict] = {}
OVERLAPS: list[dict] = []
TASK_AUDIT: list[dict] = []
NOTIFICATIONS: list[dict] = []
STANDARD_BILLING_RATE = 1500.0


def _log(event: str, payload: dict):
    TASK_AUDIT.append({"event": event, "at": datetime.utcnow(), **payload})


def _task_sla_due(priority: PriorityType, showstopper: bool, at: datetime, manual_hours: float | None = None):
    if manual_hours:
        return at + timedelta(hours=manual_hours)
    if showstopper:
        return at + timedelta(hours=24)
    days = 7 if priority == PriorityType.low else 3
    return at + timedelta(days=days)


def _task_jobs(task_id: int) -> list[dict]:
    return [j for j in JOBS.values() if j["task_id"] == task_id]


def _dependency_met(dep: dict) -> bool:
    if dep["dependency_type"] == DependencyType.task:
        parent = TASKS.get(dep["dependency_id"])
        return bool(parent and parent["status"] == "COMPLETED")
    parent = JOBS.get(dep["dependency_id"])
    return bool(parent and parent["status"] == "COMPLETED")


def _recalculate_job_cost(job: dict):
    total_hours = sum(ts["duration_hours"] for ts in TIMESHEETS.values() if ts["job_id"] == job["job_id"])
    job["actual_hours"] = total_hours
    job["actual_cost"] = round(total_hours * job["hourly_rate"], 2)


def _recalculate_task(task: dict):
    jobs = _task_jobs(task["task_id"])
    task["total_hours"] = round(sum(j["actual_hours"] for j in jobs), 2)
    task["total_cost"] = round(sum(j["actual_cost"] for j in jobs), 2)

    completed_jobs = len([j for j in jobs if j["status"] == "COMPLETED"])
    task["progress_pct"] = 0 if not jobs else round((completed_jobs * 100) / len(jobs), 2)

    expected_billing = round(task["total_hours"] * STANDARD_BILLING_RATE, 2)
    actual_billing = 0.0
    if task["is_billable"]:
        if task["billing_type"] == BillingType.fixed:
            actual_billing = task.get("billing_amount") or 0.0
        else:
            actual_billing = expected_billing

    task["expected_billing"] = expected_billing
    task["actual_billing"] = round(actual_billing, 2)
    task["profitability"] = round(task["actual_billing"] - task["total_cost"], 2)
    if task["estimated_hours"]:
        task["efficiency_pct"] = round((task["estimated_hours"] / max(task["total_hours"], 0.01)) * 100, 2)
    else:
        task["efficiency_pct"] = 0.0


def _sla_indicator(due_at: datetime):
    now = datetime.utcnow()
    if now >= due_at:
        return "BREACHED"
    if now >= due_at - timedelta(days=1):
        return "WARNING"
    return "ON_TRACK"


@router.get("/rbac/permissions")
def task_permissions():
    return {"module": "Task Management", "permissions": PERMISSIONS}


@router.get("")
def list_tasks(
    project_id: int | None = None,
    phase_name: str | None = None,
    employee: str | None = None,
    priority: PriorityType | None = None,
    status: str | None = None,
    start_from: date | None = None,
    end_to: date | None = None,
):
    rows = list(TASKS.values())
    if project_id is not None:
        rows = [r for r in rows if r["project_id"] == project_id]
    if phase_name:
        rows = [r for r in rows if r["phase_name"] == phase_name]
    if employee:
        rows = [r for r in rows if any(m["employee_name"] == employee for m in r["team_members"])]
    if priority:
        rows = [r for r in rows if r["priority"] == priority]
    if status and status != "ALL":
        rows = [r for r in rows if r["status"] == status]
    if start_from:
        rows = [r for r in rows if r["start_date"] >= start_from]
    if end_to:
        rows = [r for r in rows if r["due_date"] <= end_to]

    for row in rows:
        _recalculate_task(row)

    return rows


@router.post("")
def create_task(payload: TaskCreateRequest):
    if payload.has_dependency and not payload.dependency:
        raise HTTPException(status_code=422, detail="Dependency details required when has_dependency is true")
    if payload.project_id <= 0:
        raise HTTPException(status_code=422, detail="No task without project")
    if payload.has_dependency and payload.dependency and not _dependency_met(payload.dependency.model_dump()):
        raise HTTPException(status_code=422, detail="Task dependency is not completed")
    task_master = get_task_master(payload.task_master_id)

    now = datetime.utcnow()
    next_id = len(TASKS) + 1
    task_name = payload.task_name or task_master["task_name"]
    task = {
        "task_id": next_id,
        **payload.model_dump(),
        "task_name": task_name,
        "status": "DRAFT",
        "created_at": now,
        "updated_at": now,
        "sla_started_at": now,
        "sla_due_at": _task_sla_due(payload.priority, payload.showstopper, now, payload.sla_manual_hours),
        "sla_state": "RUNNING",
        "total_hours": 0.0,
        "total_cost": 0.0,
        "progress_pct": 0.0,
        "expected_billing": 0.0,
        "actual_billing": 0.0,
        "profitability": 0.0,
        "efficiency_pct": 0.0,
    }
    TASKS[next_id] = task

    overestimation_warning = None
    if payload.estimated_hours > task_master["standard_hours"]:
        approval = trigger_approval_request(
            ApprovalTriggerRequest(
                module=ApprovalModule.task,
                reference_id=next_id,
                creator_user_id=1,
                employee_name=payload.task_owner,
                project_name=str(payload.project_id),
                context={
                    "standard_hours": task_master["standard_hours"],
                    "planned_hours": payload.estimated_hours,
                    "warning": "This task typically takes fewer hours than planned.",
                },
            )
        )
        overestimation_warning = (
            f"This task typically takes {task_master['standard_hours']} hours. "
            f"Current estimate {payload.estimated_hours} exceeds standard."
        )
        task["estimation_approval_state"] = approval["state"]
        task["estimation_approval_id"] = approval.get("approval_id")

    # Auto Job creation: one job per assigned employee
    for member in payload.team_members:
        job_id = len(JOBS) + 1
        JOBS[job_id] = {
            "job_id": job_id,
            "task_id": next_id,
            "job_name": f"{payload.task_name} - {member.employee_name}",
            "employee": member.employee_name,
            "hourly_rate": member.hourly_rate,
            "start_date": payload.start_date,
            "due_date": payload.due_date,
            "status": "DRAFT",
            "sla_started_at": now,
            "sla_due_at": _task_sla_due(payload.priority, payload.showstopper, now, payload.sla_manual_hours),
            "sla_state": "RUNNING",
            "dependency": payload.dependency.model_dump() if payload.dependency else None,
            "actual_hours": 0.0,
            "actual_cost": 0.0,
            "timesheet_count": 0,
        }
        _log("JOB_AUTO_CREATED", {"task_id": next_id, "job_id": job_id, "employee": member.employee_name})

    _recalculate_task(task)
    _log("TASK_CREATED", {"task_id": next_id, "project_id": payload.project_id})
    NOTIFICATIONS.append(
        {
            "event": "TASK_CREATED",
            "task_id": next_id,
            "owners": [m.employee_name for m in payload.team_members],
            "message": "Task created and jobs auto-assigned",
            "at": now,
        }
    )
    task["benchmark"] = {
        "task_group": TASK_GROUPS[task_master["task_group_id"]]["group_name"],
        "standard_hours": task_master["standard_hours"],
        "historical_average": task_master["historical_average"],
        "warning": overestimation_warning,
    }
    return task


@router.get("/{task_id}")
def get_task(task_id: int):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _recalculate_task(task)
    return {**task, "jobs": _task_jobs(task_id)}


@router.put("/{task_id}")
def update_task(task_id: int, payload: TaskUpdateRequest):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updates = payload.model_dump(exclude_none=True)
    task.update(updates)
    task["updated_at"] = datetime.utcnow()
    _recalculate_task(task)
    _log("TASK_UPDATED", {"task_id": task_id, "fields": sorted(updates.keys())})
    return task


@router.patch("/{task_id}/status")
def update_task_status(task_id: int, payload: TaskStatusUpdateRequest):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.get("dependency") and payload.status in {"IN_PROGRESS", "ASSIGNED"} and not _dependency_met(task["dependency"]):
        raise HTTPException(status_code=422, detail="Cannot start task if dependency incomplete")

    if payload.status == "COMPLETED":
        open_jobs = [j for j in _task_jobs(task_id) if j["status"] != "COMPLETED"]
        if open_jobs:
            raise HTTPException(status_code=422, detail="Cannot complete task while jobs are pending")

    transition_data = validate_status_transition(
        module=ModuleType.task,
        from_status=task["status"],
        to_status=payload.status,
        actor_role=payload.actor_role,
        approval_granted=payload.approval_granted,
    )

    next_status = transition_data["next_status_def"]
    if next_status["pause_sla"]:
        task["sla_state"] = "PAUSED"
        task["sla_paused_at"] = datetime.utcnow()
    elif next_status["resume_sla"] and task.get("sla_paused_at"):
        pause_elapsed = datetime.utcnow() - task["sla_paused_at"]
        task["sla_due_at"] = task["sla_due_at"] + pause_elapsed
        task["sla_paused_at"] = None
        task["sla_state"] = "RUNNING"

    task["status"] = payload.status
    task["updated_at"] = datetime.utcnow()
    if datetime.utcnow() > task["sla_due_at"] and payload.status != "COMPLETED":
        task["sla_state"] = "BREACHED"

    if payload.status == "COMPLETED":
        approval = trigger_approval_request(
            ApprovalTriggerRequest(
                module=ApprovalModule.task,
                reference_id=task_id,
                creator_user_id=1,
                employee_name=task["task_owner"],
                project_name=str(task["project_id"]),
            )
        )
        if not approval["final"]:
            task["status"] = "PENDING_APPROVAL"
            task["approval_id"] = approval["approval_id"]
        else:
            update_task_master_learning(task["task_master_id"], task["total_hours"])

    _log("TASK_STATUS_CHANGED", {"task_id": task_id, "to": payload.status, "actor": payload.actor})
    return task


@router.get("/{task_id}/jobs")
def list_jobs(task_id: int):
    get_task(task_id)
    return _task_jobs(task_id)


@router.patch("/jobs/{job_id}/status")
def update_job_status(job_id: int, payload: JobStatusUpdateRequest):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if payload.status == "COMPLETED":
        ts_count = len([t for t in TIMESHEETS.values() if t["job_id"] == job_id])
        if ts_count == 0:
            raise HTTPException(status_code=422, detail="Cannot complete job without minimum timesheet entry")

    transition_data = validate_status_transition(
        module=ModuleType.job,
        from_status=job["status"],
        to_status=payload.status,
        actor_role=payload.actor_role,
        approval_granted=payload.approval_granted,
    )
    next_status = transition_data["next_status_def"]

    if next_status["pause_sla"]:
        job["sla_state"] = "PAUSED"
        job["sla_paused_at"] = datetime.utcnow()
    elif next_status["resume_sla"] and job.get("sla_paused_at"):
        pause_elapsed = datetime.utcnow() - job["sla_paused_at"]
        job["sla_due_at"] = job["sla_due_at"] + pause_elapsed
        job["sla_paused_at"] = None
        job["sla_state"] = "RUNNING"

    job["status"] = payload.status
    if datetime.utcnow() > job["sla_due_at"] and payload.status != "COMPLETED":
        job["sla_state"] = "BREACHED"

    if payload.status == "COMPLETED":
        approval = trigger_approval_request(
            ApprovalTriggerRequest(
                module=ApprovalModule.job,
                reference_id=job_id,
                creator_user_id=1,
                employee_name=job["employee"],
                project_name=str(TASKS[job["task_id"]]["project_id"]),
            )
        )
        if not approval["final"]:
            job["status"] = "PENDING_APPROVAL"
            job["approval_id"] = approval["approval_id"]

    _recalculate_job_cost(job)
    task = TASKS[job["task_id"]]
    _recalculate_task(task)
    _log("JOB_STATUS_CHANGED", {"job_id": job_id, "task_id": job["task_id"], "to": payload.status})
    return job


@router.post("/timesheets")
def create_timesheet(payload: TimesheetCreateRequest):
    job = JOBS.get(payload.job_id)
    if not job:
        raise HTTPException(status_code=422, detail="No timesheet without job")
    if job["status"] == "COMPLETED":
        raise HTTPException(status_code=422, detail="Cannot log time on closed job")
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=422, detail="Start must be before end")
    if payload.employee != job["employee"]:
        raise HTTPException(status_code=422, detail="Employee must match assigned job owner")

    duration_hours = round(
        (datetime.combine(payload.entry_date, payload.end_time) - datetime.combine(payload.entry_date, payload.start_time)).total_seconds() / 3600,
        2,
    )

    # Overlap detection (allow + flag)
    overlap_matches = []
    for ts in TIMESHEETS.values():
        if ts["employee"] != payload.employee or ts["entry_date"] != payload.entry_date:
            continue
        if payload.start_time < ts["end_time"] and payload.end_time > ts["start_time"]:
            overlap_matches.append(ts)

    next_id = len(TIMESHEETS) + 1
    row = {
        "timesheet_id": next_id,
        **payload.model_dump(),
        "duration_hours": duration_hours,
        "overlap_flag": bool(overlap_matches),
        "created_at": datetime.utcnow(),
    }
    TIMESHEETS[next_id] = row

    if overlap_matches:
        OVERLAPS.append(
            {
                "employee": payload.employee,
                "entry_date": payload.entry_date,
                "timesheet_id": next_id,
                "overlaps_with": [m["timesheet_id"] for m in overlap_matches],
                "overlap_duration_hours": min(duration_hours, sum(m["duration_hours"] for m in overlap_matches)),
            }
        )

    job["timesheet_count"] += 1
    _recalculate_job_cost(job)
    task = TASKS[job["task_id"]]
    _recalculate_task(task)

    # Cost & profit alerts
    if task["total_cost"] > task["estimated_cost"]:
        NOTIFICATIONS.append(
            {
                "event": "COST_ALERT",
                "task_id": task["task_id"],
                "message": "Actual cost exceeded planned cost",
                "at": datetime.utcnow(),
            }
        )
    if task["profitability"] < 0:
        NOTIFICATIONS.append(
            {
                "event": "PROFIT_ALERT",
                "task_id": task["task_id"],
                "message": "Task profitability is negative",
                "at": datetime.utcnow(),
            }
        )

    _log("TIMESHEET_CREATED", {"timesheet_id": next_id, "job_id": payload.job_id, "overlap": row["overlap_flag"]})
    approval = trigger_approval_request(
        ApprovalTriggerRequest(
            module=ApprovalModule.timesheet,
            reference_id=next_id,
            creator_user_id=payload.creator_user_id,
            employee_name=payload.employee,
            project_name=str(task["project_id"]),
        )
    )
    row["approval_state"] = approval["state"]
    row["approval_id"] = approval.get("approval_id")
    return row


@router.get("/timesheets")
def list_timesheets(job_id: int | None = None, employee: str | None = None, overlap_only: bool = False):
    rows = list(TIMESHEETS.values())
    if job_id is not None:
        rows = [r for r in rows if r["job_id"] == job_id]
    if employee:
        rows = [r for r in rows if r["employee"] == employee]
    if overlap_only:
        rows = [r for r in rows if r["overlap_flag"]]
    return rows


@router.get("/timesheets/overlap-report")
def overlap_report(scope: str = "ADMIN", manager: str | None = None):
    if scope == "MANAGER" and manager:
        team = {
            j["employee"]
            for j in JOBS.values()
            if TASKS[j["task_id"]]["task_owner"] == manager
        }
        return [r for r in OVERLAPS if r["employee"] in team]
    return OVERLAPS


@router.get("/{task_id}/costing")
def task_costing(task_id: int):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _recalculate_task(task)
    planned_cost = task["estimated_cost"]
    actual_cost = task["total_cost"]

    return {
        "task_id": task_id,
        "planned_cost": planned_cost,
        "actual_cost": actual_cost,
        "expected_billing": task["expected_billing"],
        "actual_billing": task["actual_billing"],
        "profitability": task["profitability"],
        "efficiency_pct": task["efficiency_pct"],
        "standard_billing_rate": STANDARD_BILLING_RATE,
    }


@router.post("/billing/finalize")
def finalize_billing(payload: BillingFinalizeRequest):
    task = TASKS.get(payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["billing_amount"] = payload.billing_amount
    task["billing_type"] = BillingType.fixed
    task["is_billable"] = True
    _recalculate_task(task)

    approval = trigger_approval_request(
        ApprovalTriggerRequest(
            module=ApprovalModule.billing,
            reference_id=payload.task_id,
            creator_user_id=payload.creator_user_id,
            employee_name=task["task_owner"],
            project_name=str(task["project_id"]),
            context={
                "actual_cost": task["total_cost"],
                "expected_billing": task["expected_billing"],
                "entered_billing": payload.billing_amount,
            },
        )
    )
    task["billing_approval_state"] = approval["state"]
    task["billing_approval_id"] = approval.get("approval_id")
    return task


@router.get("/dashboard/summary")
def task_dashboard():
    rows = list(TASKS.values())
    for task in rows:
        _recalculate_task(task)

    return {
        "execution": {
            "tasks_total": len(rows),
            "jobs_total": len(JOBS),
            "timesheets_total": len(TIMESHEETS),
        },
        "sla": {
            "on_track": len([t for t in rows if _sla_indicator(t["sla_due_at"]) == "ON_TRACK"]),
            "warning": len([t for t in rows if _sla_indicator(t["sla_due_at"]) == "WARNING"]),
            "breached": len([t for t in rows if _sla_indicator(t["sla_due_at"]) == "BREACHED"]),
        },
        "financial": {
            "planned_cost": round(sum(t["estimated_cost"] for t in rows), 2),
            "actual_cost": round(sum(t["total_cost"] for t in rows), 2),
            "expected_billing": round(sum(t["expected_billing"] for t in rows), 2),
            "actual_billing": round(sum(t["actual_billing"] for t in rows), 2),
            "profitability": round(sum(t["profitability"] for t in rows), 2),
        },
        "progress": {
            "avg_progress_pct": 0 if not rows else round(sum(t["progress_pct"] for t in rows) / len(rows), 2),
        },
    }


@router.get("/reports/summary")
def task_reports():
    rows = list(TASKS.values())
    for task in rows:
        _recalculate_task(task)

    return {
        "task_summary": {
            "total": len(rows),
            "completed": len([t for t in rows if t["status"] == "COMPLETED"]),
        },
        "task_cost_report": [
            {
                "task_id": t["task_id"],
                "task_name": t["task_name"],
                "planned_cost": t["estimated_cost"],
                "actual_cost": t["total_cost"],
                "profitability": t["profitability"],
            }
            for t in rows
        ],
        "job_performance_report": [
            {
                "job_id": j["job_id"],
                "employee": j["employee"],
                "hours": j["actual_hours"],
                "cost": j["actual_cost"],
                "status": j["status"],
            }
            for j in JOBS.values()
        ],
        "employee_productivity": [
            {
                "employee": employee,
                "hours": round(sum(j["actual_hours"] for j in JOBS.values() if j["employee"] == employee), 2),
            }
            for employee in sorted({j["employee"] for j in JOBS.values()})
        ],
        "sla_compliance": task_dashboard()["sla"],
    }


@router.get("/analytics/summary")
def task_analytics():
    rows = list(TASKS.values())
    for task in rows:
        _recalculate_task(task)

    return {
        "cost_vs_estimate": [
            {
                "task_id": t["task_id"],
                "estimated": t["estimated_cost"],
                "actual": t["total_cost"],
            }
            for t in rows
        ],
        "time_variance_hours": [
            {
                "task_id": t["task_id"],
                "estimated_hours": t["estimated_hours"],
                "actual_hours": t["total_hours"],
            }
            for t in rows
        ],
        "resource_utilization": [
            {
                "employee": employee,
                "hours": round(sum(j["actual_hours"] for j in JOBS.values() if j["employee"] == employee), 2),
            }
            for employee in sorted({j["employee"] for j in JOBS.values()})
        ],
        "delay_reasons": ["Dependency Block", "SLA Pause", "Pending Approval"],
        "overlap_trends": {
            "entries_with_overlap": len([t for t in TIMESHEETS.values() if t["overlap_flag"]]),
            "overlap_records": len(OVERLAPS),
        },
        "avg_task_time_by_group": [
            {
                "task_group": group["group_name"],
                "average_hours": round(
                    sum(
                        t["total_hours"]
                        for t in TASKS.values()
                        if TASK_MASTER[t["task_master_id"]]["task_group_id"] == group_id
                    )
                    / max(
                        1,
                        len([t for t in TASKS.values() if TASK_MASTER[t["task_master_id"]]["task_group_id"] == group_id]),
                    ),
                    2,
                ),
            }
            for group_id, group in TASK_GROUPS.items()
        ],
        "efficiency_trends": [
            {
                "task_id": t["task_id"],
                "estimated_hours": t["estimated_hours"],
                "actual_hours": t["total_hours"],
                "efficiency_pct": t["efficiency_pct"],
            }
            for t in rows
        ],
        "capacity_utilization": workload_summary(),
        "productivity_variance": [
            {
                "employee": employee,
                "actual_hours": round(sum(j["actual_hours"] for j in JOBS.values() if j["employee"] == employee), 2),
            }
            for employee in sorted({j["employee"] for j in JOBS.values()})
        ],
    }


@router.get("/notifications")
def task_notifications():
    return NOTIFICATIONS


@router.get("/audit-log")
def task_audit_log():
    return TASK_AUDIT


@router.get("/workload/summary")
def workload_summary():
    employee_allocated: dict[str, float] = {}
    for job in JOBS.values():
        allocated = float(TASKS[job["task_id"]]["estimated_hours"]) / max(1, len(_task_jobs(job["task_id"])))
        employee_allocated[job["employee"]] = employee_allocated.get(job["employee"], 0.0) + allocated

    available_hours = 8.0
    rows = []
    for employee, allocated in employee_allocated.items():
        utilization_pct = round((allocated / available_hours) * 100, 2)
        if utilization_pct < 50:
            status = "UNDERUTILIZED"
        elif utilization_pct <= 85:
            status = "OPTIMALLY_UTILIZED"
        elif utilization_pct <= 100:
            status = "FULLY_UTILIZED"
        else:
            status = "OVERUTILIZED"
        rows.append(
            {
                "employee": employee,
                "allocated_hours": round(allocated, 2),
                "available_hours": available_hours,
                "utilization_pct": utilization_pct,
                "status": status,
            }
        )
    return rows


@router.get("/ai/suggestions")
def ai_scheduling_suggestions(task_master_id: int, planned_hours: float, priority: PriorityType):
    task_master = get_task_master(task_master_id)
    workloads = workload_summary()
    sorted_candidates = sorted(workloads, key=lambda x: x["utilization_pct"])
    best_candidate = sorted_candidates[0] if sorted_candidates else None

    return {
        "task_master": task_master["task_name"],
        "priority": priority,
        "benchmark_hours": task_master["standard_hours"],
        "historical_average": task_master["historical_average"],
        "planned_hours": planned_hours,
        "suggestions": {
            "assign_to": best_candidate["employee"] if best_candidate else None,
            "capacity_status": best_candidate["status"] if best_candidate else None,
            "reassignment_hint": "Reassign from overloaded employee" if any(w["status"] == "OVERUTILIZED" for w in workloads) else "Current balance is acceptable",
            "next_available_slot_hint": "Use /calendar-intelligence/suggestions/next-slot for exact slot suggestion",
        },
        "efficiency_warning": (
            f"Similar tasks were completed in ~{task_master['historical_average']} hrs. Current estimate = {planned_hours} hrs."
            if planned_hours > task_master["historical_average"]
            else None
        ),
    }


@router.post("/create")
def create_task_action(payload: TaskCreateRequest):
    return create_task(payload)


@router.post("/jobs/update-status")
def update_job_status_action(job_id: int, payload: JobStatusUpdateRequest):
    return update_job_status(job_id, payload)


@router.post("/timesheets/add")
def add_timesheet_action(payload: TimesheetCreateRequest):
    return create_timesheet(payload)


@router.get("/list")
def list_tasks_contract(
    project_id: int | None = None,
    status: str | None = None,
    priority: PriorityType | None = None,
    assignee: str | None = None,
):
    return {"count": len(list_tasks(project_id=project_id, employee=assignee, priority=priority, status=status)), "items": list_tasks(project_id=project_id, employee=assignee, priority=priority, status=status)}


@router.post("/search")
def search_tasks(payload: dict):
    return list_tasks_contract(
        project_id=payload.get("projectId"),
        status=payload.get("status"),
        assignee=payload.get("assignee"),
        priority=payload.get("priority"),
    )


@router.post("/start/{task_id}")
def start_task_contract(task_id: int):
    return update_task_status(task_id, TaskStatusUpdateRequest(status="IN_PROGRESS", actor="SYSTEM", actor_role="Admin"))


@router.post("/complete/{task_id}")
def complete_task_contract(task_id: int):
    return update_task_status(task_id, TaskStatusUpdateRequest(status="COMPLETED", actor="SYSTEM", actor_role="Admin"))


@router.post("/close/{task_id}")
def close_task_contract(task_id: int):
    return update_task_status(task_id, TaskStatusUpdateRequest(status="CLOSED", actor="SYSTEM", actor_role="Admin", approval_granted=True))


@router.post("/reassign/{task_id}")
def reassign_task_contract(task_id: int, assignee: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not any(member["employee_name"] == assignee for member in task["team_members"]):
        task["team_members"].append({"employee_name": assignee, "hourly_rate": 0})
    task["task_owner"] = assignee
    _log("TASK_REASSIGNED", {"task_id": task_id, "assignee": assignee})
    return task


@router.put("/update/{task_id}")
def update_task_contract(task_id: int, payload: TaskUpdateRequest):
    return update_task(task_id, payload)


@router.post("/block/{task_id}")
def block_task_contract(task_id: int):
    return update_task_status(task_id, TaskStatusUpdateRequest(status="BLOCKED", actor="SYSTEM", actor_role="Admin"))


@router.post("/submit-approval/{task_id}")
def submit_task_approval(task_id: int):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["approval_state"] = "PENDING"
    _log("TASK_APPROVAL_SUBMITTED", {"task_id": task_id})
    return {"status": "submitted", "task_id": task_id}


@router.post("/add-job/{task_id}")
def add_job_contract(task_id: int, assignee: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    job_id = len(JOBS) + 1
    JOBS[job_id] = {
        "job_id": job_id,
        "task_id": task_id,
        "job_name": f"{task['task_name']} - {assignee}",
        "employee": assignee,
        "hourly_rate": 0,
        "start_date": task["start_date"],
        "due_date": task["due_date"],
        "status": "DRAFT",
        "sla_started_at": datetime.utcnow(),
        "sla_due_at": task["sla_due_at"],
        "sla_state": "RUNNING",
        "dependency": None,
        "actual_hours": 0.0,
        "actual_cost": 0.0,
        "timesheet_count": 0,
    }
    _log("JOB_ADDED", {"task_id": task_id, "job_id": job_id})
    return JOBS[job_id]
