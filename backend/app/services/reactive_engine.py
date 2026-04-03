from __future__ import annotations

from datetime import date, datetime


def recalculate_project_dates(tasks: list[dict], jobs: list[dict]) -> dict:
    task_start_dates = [t.get("start_date") for t in tasks if t.get("start_date")]
    job_end_dates = [j.get("end_date") for j in jobs if j.get("end_date")]
    project_start = min(task_start_dates) if task_start_dates else None
    project_end = max(job_end_dates) if job_end_dates else None
    return {"project_start_date": project_start, "project_end_date": project_end}


def validate_deadline_extension(old_date: date | None, new_date: date, actor_role: str, reason: str | None) -> dict:
    if actor_role not in {"Admin", "SuperAdmin"}:
        return {"allowed": False, "error": "Only Admin/SuperAdmin may edit deadlines"}
    if old_date and new_date < old_date:
        return {"allowed": False, "error": "Deadline cannot be reduced"}
    if old_date and new_date > old_date and not reason:
        return {"allowed": False, "error": "Rollover reason is required for extension"}
    return {
        "allowed": True,
        "is_rollover": bool(old_date and new_date > old_date),
        "rollover_reason": reason,
        "rolled_at": datetime.utcnow(),
    }


def dependency_can_start(parent_status: str) -> bool:
    return parent_status in {"COMPLETED", "DONE", "CLOSED"}


def detect_timesheet_overlap(new_entry: dict, existing_entries: list[dict]) -> bool:
    user = new_entry.get("user_name")
    date_value = new_entry.get("date")
    start = new_entry.get("start_time")
    end = new_entry.get("end_time")
    for row in existing_entries:
        if row.get("user_name") != user or row.get("date") != date_value:
            continue
        if start < row.get("end_time") and end > row.get("start_time"):
            return True
    return False


def workload_band(utilization_pct: float) -> str:
    if utilization_pct < 60:
        return "UNDERUTILIZED"
    if utilization_pct < 85:
        return "OPTIMAL"
    if utilization_pct <= 100:
        return "FULLY_UTILIZED"
    return "OVERUTILIZED"


def costing_metrics(hours_spent: float, planned_hours: float, hourly_cost: float, billed_amount: float) -> dict:
    actual_cost = round(hours_spent * hourly_cost, 2)
    expected_cost = round(planned_hours * 1500, 2)
    profitability = round(billed_amount - actual_cost, 2)
    return {
        "actual_cost": actual_cost,
        "expected_cost": expected_cost,
        "profitability": profitability,
    }


def approval_chain(approval_required: bool, reporting_manager: str | None, department_poc: str | None) -> list[str]:
    if not approval_required:
        return []
    chain = [x for x in [reporting_manager, department_poc] if x]
    return chain
