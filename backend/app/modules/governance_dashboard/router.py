from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.tasks.router import TASKS, JOBS, TIMESHEETS, workload_summary
from app.modules.projects.router import PROJECTS
from app.modules.approval.router import APPROVALS, ApprovalState
from app.modules.gamification.router import admin_scoreboard

router = APIRouter(prefix="/governance-dashboard", tags=["Governance Dashboard"])


SUGGESTED_WIDGETS = [
    "TASK_STATUS_DISTRIBUTION",
    "SLA_COMPLIANCE",
    "ROLLOVER_SUMMARY",
    "EMPLOYEE_UTILIZATION",
    "TOP_DELAYING_EMPLOYEES",
    "PROJECT_PROFITABILITY",
    "COST_LEAKAGE",
    "TIMESHEET_OVERLAP_REPORT",
    "APPROVAL_BOTTLENECK",
    "WORKLOAD_HEATMAP",
    "UPCOMING_DEADLINES",
    "AT_RISK_PROJECTS",
]


class DashboardConfigRequest(BaseModel):
    user_id: int
    role: str
    active_widgets: list[str] = Field(default_factory=list)
    locked_widgets: list[str] = Field(default_factory=list)


DASHBOARD_CONFIGS: dict[int, dict] = {}
WIDGET_USAGE: list[dict] = []


def _sla_widget():
    total = len(TASKS)
    breached = len([t for t in TASKS.values() if t.get("sla_state") == "BREACHED"])
    return {
        "on_time_pct": 0 if not total else round(((total - breached) * 100) / total, 2),
        "breached_pct": 0 if not total else round((breached * 100) / total, 2),
    }


def _task_status_widget():
    distribution: dict[str, int] = {}
    for t in TASKS.values():
        distribution[t["status"]] = distribution.get(t["status"], 0) + 1
    return distribution


def _project_profitability_widget():
    return [
        {
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "estimated_cost": p["estimated_cost"],
            "actual_cost": p["actual_cost"],
            "profitability": p["estimated_cost"] - p["actual_cost"],
        }
        for p in PROJECTS.values()
    ]


def _cost_leakage_widget():
    return [
        {
            "task_id": t["task_id"],
            "planned_cost": t["estimated_cost"],
            "actual_cost": t["total_cost"],
            "leakage": t["total_cost"] - t["estimated_cost"],
        }
        for t in TASKS.values()
    ]


def _approval_bottleneck_widget():
    return {
        "pending_l1": len([a for a in APPROVALS.values() if a["state"] == ApprovalState.pending_l1]),
        "pending_l2": len([a for a in APPROVALS.values() if a["state"] == ApprovalState.pending_l2]),
    }


def _upcoming_deadlines_widget():
    upcoming = sorted(TASKS.values(), key=lambda x: x["due_date"])[:10]
    return [{"task_id": t["task_id"], "task_name": t["task_name"], "due_date": t["due_date"]} for t in upcoming]


def _timesheet_overlap_widget():
    overlaps = [t for t in TIMESHEETS.values() if t.get("overlap_flag")]
    per_employee: dict[str, int] = {}
    for row in overlaps:
        per_employee[row["employee"]] = per_employee.get(row["employee"], 0) + 1
    return {"daily_overlap_count": len(overlaps), "employee_wise": per_employee}


def _top_delaying_employees_widget():
    board = admin_scoreboard()
    return sorted(board, key=lambda x: x["delays"]["jobs_delayed"], reverse=True)[:10]


def _workload_heatmap_widget():
    return workload_summary()


def _at_risk_projects_widget():
    return [
        {
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "status": p["status"],
            "health_status": p["health_status"],
            "at_risk": p["health_status"] in {"AT_RISK", "DELAYED"},
        }
        for p in PROJECTS.values()
    ]


@router.get("/suggested-widgets")
def suggested_widgets():
    return SUGGESTED_WIDGETS


@router.get("/config/{user_id}")
def get_dashboard_config(user_id: int):
    return DASHBOARD_CONFIGS.get(
        user_id,
        {
            "user_id": user_id,
            "role": "Admin",
            "active_widgets": SUGGESTED_WIDGETS[:6],
            "locked_widgets": [],
        },
    )


@router.put("/config/{user_id}")
def update_dashboard_config(user_id: int, payload: DashboardConfigRequest):
    if payload.role not in {"Admin", "Super Admin"}:
        raise HTTPException(status_code=403, detail="Only Admin/Super Admin can configure governance dashboard")

    DASHBOARD_CONFIGS[user_id] = payload.model_dump()
    return DASHBOARD_CONFIGS[user_id]


@router.get("/main/{user_id}")
def governance_dashboard_main(user_id: int):
    cfg = get_dashboard_config(user_id)
    widgets = {}

    if "TASK_STATUS_DISTRIBUTION" in cfg["active_widgets"]:
        widgets["task_status_distribution"] = _task_status_widget()
    if "SLA_COMPLIANCE" in cfg["active_widgets"]:
        widgets["sla_compliance"] = _sla_widget()
    if "EMPLOYEE_UTILIZATION" in cfg["active_widgets"]:
        widgets["employee_utilization"] = workload_summary()
    if "PROJECT_PROFITABILITY" in cfg["active_widgets"]:
        widgets["project_profitability"] = _project_profitability_widget()
    if "COST_LEAKAGE" in cfg["active_widgets"]:
        widgets["cost_leakage"] = _cost_leakage_widget()
    if "APPROVAL_BOTTLENECK" in cfg["active_widgets"]:
        widgets["approval_bottleneck"] = _approval_bottleneck_widget()
    if "UPCOMING_DEADLINES" in cfg["active_widgets"]:
        widgets["upcoming_deadlines"] = _upcoming_deadlines_widget()
    if "TIMESHEET_OVERLAP_REPORT" in cfg["active_widgets"]:
        widgets["timesheet_overlap_report"] = _timesheet_overlap_widget()
    if "TOP_DELAYING_EMPLOYEES" in cfg["active_widgets"]:
        widgets["top_delaying_employees"] = _top_delaying_employees_widget()
    if "WORKLOAD_HEATMAP" in cfg["active_widgets"]:
        widgets["workload_heatmap"] = _workload_heatmap_widget()
    if "AT_RISK_PROJECTS" in cfg["active_widgets"]:
        widgets["at_risk_projects"] = _at_risk_projects_widget()

    WIDGET_USAGE.append({"user_id": user_id, "at": datetime.utcnow(), "widgets": list(widgets.keys())})
    return {"config": cfg, "widgets": widgets}


@router.get("/analytics/usage")
def governance_widget_analytics():
    view_counts: dict[str, int] = {}
    enable_counts: dict[str, int] = {w: 0 for w in SUGGESTED_WIDGETS}

    for entry in WIDGET_USAGE:
        for widget in entry["widgets"]:
            view_counts[widget] = view_counts.get(widget, 0) + 1

    for cfg in DASHBOARD_CONFIGS.values():
        for widget in cfg["active_widgets"]:
            enable_counts[widget] = enable_counts.get(widget, 0) + 1

    return {
        "most_viewed_widgets": sorted(view_counts.items(), key=lambda x: x[1], reverse=True),
        "most_enabled_widgets": sorted(enable_counts.items(), key=lambda x: x[1], reverse=True),
        "admin_usage_behavior": {"config_updates": len(DASHBOARD_CONFIGS), "dashboard_views": len(WIDGET_USAGE)},
    }


@router.get("/export")
def export_widget(widget_name: str, format: str = "excel"):
    payload = governance_dashboard_main(1)["widgets"].get(widget_name)
    if payload is None:
        raise HTTPException(status_code=404, detail="Widget not found in dashboard")
    if format not in {"excel", "pdf"}:
        raise HTTPException(status_code=422, detail="Unsupported export format")
    return {"widget": widget_name, "format": format, "data": payload}
