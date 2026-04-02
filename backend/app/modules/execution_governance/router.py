from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.event_bus import publish_event
from app.modules.projects.router import PROJECTS
from app.modules.tasks.router import JOBS, TASKS, TIMESHEETS
from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry
from app.services.interconnect_registry import coverage_matrix, mark_covered, uncovered
from app.services.reactive_engine import (
    approval_chain,
    costing_metrics,
    dependency_can_start,
    detect_timesheet_overlap,
    recalculate_project_dates,
    validate_deadline_extension,
    workload_band,
)

router = APIRouter(prefix="/execution-governance", tags=["Execution Governance"])


class GlobalFilter(BaseModel):
    company: str | None = None
    branch: str | None = None
    department: str | None = None
    employee: str | None = None
    client: str | None = None
    project: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    priority: str | None = None


class DeadlineRuleRequest(BaseModel):
    old_date: date | None = None
    new_date: date
    actor_role: str
    reason: str | None = None


@router.get("/interconnect/coverage")
def interconnect_coverage():
    return {"matrix": coverage_matrix(), "uncovered": uncovered(), "coverage_pct": round((len(coverage_matrix()) - len(uncovered())) / len(coverage_matrix()) * 100, 2)}


@router.post("/interconnect/mark-covered")
def mark_interconnect(source: str, target: str, source_ref: str = "manual"):
    mark_covered(source, target, source_ref)
    add_audit_entry(
        AuditCreateRequest(
            user_name="SYSTEM",
            module="INTERCONNECT",
            reference_id=f"{source}->{target}",
            action_type="COVERAGE_MARKED",
            new_value={"source_ref": source_ref},
        )
    )
    return {"status": "ok"}


@router.get("/reactive/project-dates/{project_id}")
def project_date_reactive(project_id: int):
    tasks = [t for t in TASKS.values() if t.get("project_id") == project_id]
    jobs = [j for j in JOBS.values() if any(t.get("task_id") == j.get("task_id") for t in tasks)]
    result = recalculate_project_dates(tasks, jobs)
    if project_id in PROJECTS:
        PROJECTS[project_id]["start_date"] = result["project_start_date"] or PROJECTS[project_id].get("start_date")
        PROJECTS[project_id]["end_date"] = result["project_end_date"] or PROJECTS[project_id].get("end_date")
    return result


@router.post("/reactive/deadline-rules")
def deadline_rules(payload: DeadlineRuleRequest):
    result = validate_deadline_extension(payload.old_date, payload.new_date, payload.actor_role, payload.reason)
    if result.get("allowed") and result.get("is_rollover"):
        publish_event("ROLLOVER_CREATED", {"new_date": str(payload.new_date), "reason": payload.reason})
    return result


@router.get("/reactive/dependency-check")
def dependency_check(parent_status: str):
    can_start = dependency_can_start(parent_status)
    if can_start:
        publish_event("DEPENDENCY_UNLOCKED", {"parent_status": parent_status})
    return {"can_start": can_start}


@router.post("/reactive/timesheet-overlap")
def overlap_check(entry: dict):
    flagged = detect_timesheet_overlap(entry, list(TIMESHEETS.values()))
    return {"save_allowed": True, "overlap_flag": flagged}


@router.get("/reactive/workload/{user_name}")
def user_workload(user_name: str, planned_hours: float = 160.0, consumed_hours: float = 0.0):
    utilization = (consumed_hours / planned_hours * 100) if planned_hours else 0.0
    return {"user_name": user_name, "utilization_pct": round(utilization, 2), "band": workload_band(utilization)}


@router.get("/reactive/costing")
def costing(hours_spent: float, planned_hours: float, hourly_cost: float, billed_amount: float):
    return costing_metrics(hours_spent, planned_hours, hourly_cost, billed_amount)


@router.get("/reactive/approval-chain")
def reactive_approval_chain(approval_required: bool, reporting_manager: str | None = None, department_poc: str | None = None):
    return {"chain": approval_chain(approval_required, reporting_manager, department_poc)}


@router.post("/reports/{module}/list")
def module_list_report(module: str, payload: GlobalFilter):
    dataset = {
        "projects": list(PROJECTS.values()),
        "tasks": list(TASKS.values()),
        "jobs": list(JOBS.values()),
        "timesheets": list(TIMESHEETS.values()),
    }.get(module.lower(), [])
    return {"module": module, "filters": payload.model_dump(), "rows": dataset}


@router.post("/reports/{module}/summary")
def module_summary_report(module: str, payload: GlobalFilter):
    rows = module_list_report(module, payload)["rows"]
    return {"module": module, "count": len(rows), "filters": payload.model_dump()}


@router.post("/reports/{module}/export")
def module_export(module: str, format: str = "excel"):
    return {"module": module, "format": format, "status": "queued"}


@router.post("/analytics/{module}")
def module_analytics(module: str, payload: GlobalFilter):
    rows = module_list_report(module, payload)["rows"]
    return {
        "module": module,
        "kpis": {
            "total": len(rows),
            "suggested_widgets": ["trend", "status_breakdown", "sla_risk"],
            "governance_toggles": ["show_sla", "show_approvals", "show_rollovers"],
        },
    }
