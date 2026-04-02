from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.collaboration.router import ensure_project_channel
from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry

router = APIRouter(prefix="/projects", tags=["Project Module"])


class ProjectStatus(str, Enum):
    draft = "DRAFT"
    active = "ACTIVE"
    on_hold = "ON_HOLD"
    delayed = "DELAYED"
    completed = "COMPLETED"
    closed = "CLOSED"


class PhaseStatus(str, Enum):
    not_started = "NOT_STARTED"
    in_progress = "IN_PROGRESS"
    on_hold = "ON_HOLD"
    completed = "COMPLETED"


class PocRequest(BaseModel):
    name: str
    email: str
    mobile: str
    poc_type: str


class PhaseRequest(BaseModel):
    phase_name: str
    start_date: date
    end_date: date
    status: PhaseStatus = PhaseStatus.not_started


class ProjectCreateRequest(BaseModel):
    project_name: str
    client_name: str
    project_manager: str
    employee_group_pocs: dict[str, str]
    start_date: date
    end_date: date
    estimated_cost: float
    estimated_hours: float
    product_service: str | None = None
    so_number: str | None = None
    invoice_number: str | None = None
    payment_terms: str | None = None
    pocs: list[PocRequest] = Field(default_factory=list)
    phases: list[PhaseRequest] = Field(default_factory=list)


class ProjectStatusUpdateRequest(BaseModel):
    status: ProjectStatus


PROJECTS: dict[int, dict] = {}
PHASES: dict[int, list[dict]] = {}

REQUIRED_GROUPS = {"Management", "Operations", "Implementation", "Support", "Development", "Accounts"}


@router.get("")
def list_projects(status: ProjectStatus | None = None):
    rows = list(PROJECTS.values())
    if status:
        rows = [r for r in rows if r["status"] == status]
    return rows


@router.post("")
def create_project(payload: ProjectCreateRequest):
    missing = sorted(REQUIRED_GROUPS - set(payload.employee_group_pocs.keys()))
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing mandatory group POCs: {missing}")

    pid = len(PROJECTS) + 1
    phases = []
    for idx, p in enumerate(payload.phases, start=1):
        phases.append({"phase_id": idx, **p.model_dump(), "progress_pct": 0.0, "cost_actual": 0.0, "hours_actual": 0.0})

    actual_cost = 0.0
    actual_hours = 0.0
    project = {
        "project_id": pid,
        **payload.model_dump(),
        "status": ProjectStatus.draft,
        "actual_cost": actual_cost,
        "actual_hours": actual_hours,
        "progress_pct": 0.0,
        "health_status": "ON_TRACK",
        "created_at": datetime.utcnow(),
        "interconnects": ["PROJECT->TASK", "PROJECT->TICKET", "PROJECT->JOB", "PROJECT->SLA", "PROJECT->COSTING"],
        "audit_log": [{"event": "PROJECT_CREATED", "at": datetime.utcnow()}],
    }
    PROJECTS[pid] = project
    PHASES[pid] = phases
    poc_members = [payload.project_manager, *payload.employee_group_pocs.values()]
    ensure_project_channel(project_id=pid, project_name=payload.project_name, members=sorted(set(poc_members)))
    add_audit_entry(
        AuditCreateRequest(
            user_name=payload.project_manager,
            module="PROJECT",
            reference_id=str(pid),
            action_type="CREATE",
            field_name=None,
            old_value=None,
            new_value={"project_name": payload.project_name},
            remarks="Project created",
        )
    )
    return project


@router.get("/{project_id}")
def get_project(project_id: int):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {**project, "phases": PHASES.get(project_id, [])}


@router.patch("/{project_id}/status")
def update_project_status(project_id: int, payload: ProjectStatusUpdateRequest):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    current = project["status"]
    if current == ProjectStatus.draft and payload.status not in {ProjectStatus.active, ProjectStatus.on_hold}:
        raise HTTPException(status_code=422, detail="Draft can transition only to Active/On Hold")
    if current == ProjectStatus.completed and payload.status != ProjectStatus.closed:
        raise HTTPException(status_code=422, detail="Completed can transition only to Closed")

    project["status"] = payload.status
    project["audit_log"].append({"event": "PROJECT_STATUS_UPDATED", "to": payload.status, "at": datetime.utcnow()})
    add_audit_entry(
        AuditCreateRequest(
            user_name="SYSTEM",
            module="PROJECT",
            reference_id=str(project_id),
            action_type="STATUS_CHANGE",
            field_name="status",
            old_value=str(current),
            new_value=str(payload.status),
            remarks=None,
        )
    )
    return project


@router.get("/{project_id}/dashboard")
def project_dashboard(project_id: int):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    phases = PHASES.get(project_id, [])
    phase_progress = sum(p["progress_pct"] for p in phases) / len(phases) if phases else 0.0
    project["progress_pct"] = phase_progress

    budget_ratio = (project["actual_cost"] / project["estimated_cost"]) if project["estimated_cost"] else 0.0
    if budget_ratio >= 1.0:
        project["health_status"] = "DELAYED"
    elif budget_ratio >= 0.8:
        project["health_status"] = "AT_RISK"
    else:
        project["health_status"] = "ON_TRACK"

    return {
        "execution": {"tasks_total": 0, "tasks_completed": 0, "tickets_open": 0, "tickets_closed": 0},
        "effort": {"total_hours": project["actual_hours"]},
        "financial": {
            "estimated_cost": project["estimated_cost"],
            "actual_cost": project["actual_cost"],
            "profitability": project["estimated_cost"] - project["actual_cost"],
        },
        "progress": {"project_progress_pct": project["progress_pct"], "health_status": project["health_status"]},
        "phase_progress": [{"phase_id": p["phase_id"], "phase_name": p["phase_name"], "progress_pct": p["progress_pct"]} for p in phases],
    }


@router.get("/{project_id}/reports/summary")
def project_reports(project_id: int):
    get_project(project_id)
    return {
        "reports": ["PROJECT_SUMMARY", "BUDGET_VS_ACTUAL", "TASK_PROGRESS", "RESOURCE_COST"],
        "analytics": ["COMPLETION_TRENDS", "COST_VARIANCE", "RESOURCE_UTILIZATION"],
    }
