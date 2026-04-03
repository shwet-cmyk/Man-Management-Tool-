from __future__ import annotations

from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class ChartType(str, Enum):
    bar = "BAR"
    line = "LINE"
    scatter = "SCATTER"
    pie = "PIE"
    table = "TABLE"
    kpi = "KPI"


class AggregationType(str, Enum):
    sum = "SUM"
    count = "COUNT"
    avg = "AVG"
    min = "MIN"
    max = "MAX"


class WidgetCreateRequest(BaseModel):
    dashboard_code: str = "DEFAULT"
    title: str = Field(..., min_length=2)
    dataset_code: str = Field(..., min_length=2)
    x_axis: str = Field(..., min_length=1)
    y_axis: str = Field(..., min_length=1)
    aggregation: AggregationType
    chart_type: ChartType
    filters: dict[str, str] = Field(default_factory=dict)


DATASETS = [
    {"dataset_code": "TASK_EXECUTION", "fields": ["task_id", "status", "assignee", "planned_hours", "actual_hours"], "roles": ["Admin", "Manager", "Analyst"]},
    {"dataset_code": "JOB_COMMERCIAL", "fields": ["job_id", "client", "billable_hours", "cost", "margin"], "roles": ["Admin", "Manager"]},
    {"dataset_code": "USER_PRODUCTIVITY", "fields": ["user_id", "department", "completed_tasks", "utilization_pct"], "roles": ["Admin", "Manager", "Analyst"]},
]

WIDGETS: dict[int, dict] = {}
LAYOUTS: dict[str, dict] = {}


def _dataset_by_code(dataset_code: str):
    for ds in DATASETS:
        if ds["dataset_code"] == dataset_code:
            return ds
    return None


@router.get("/default")
def default_dashboard(user_role: str = "Analyst"):
    return {
        "landing_dashboard": "DEFAULT_ROLE_DASHBOARD",
        "user_role": user_role,
        "widget_count": len(WIDGETS),
    }


@router.get("/layout")
def get_dashboard_layout(role: str = "User", user_id: int = 1):
    key = f"{role}:{user_id}"
    default_widgets = ["My Tasks", "SLA Alerts", "Notifications", "Recent Activity", "AI Suggestions", "Release Notes"]
    layout = LAYOUTS.get(key) or {
        "dashboard_type": role,
        "user_id": user_id,
        "widgets": default_widgets,
        "customizable": role in {"SuperAdmin", "Admin", "Manager", "Developer"},
        "updated_at": None,
    }
    return layout


@router.post("/layout/save")
def save_dashboard_layout(payload: dict):
    role = payload.get("dashboardType", "User")
    user_id = payload.get("userId", 1)
    widgets = payload.get("widgets", [])
    if not isinstance(widgets, list):
        raise HTTPException(status_code=422, detail="widgets must be a list")
    key = f"{role}:{user_id}"
    LAYOUTS[key] = {"dashboard_type": role, "user_id": user_id, "widgets": widgets, "updated_at": datetime.utcnow()}
    return {"status": "saved", "layout": LAYOUTS[key], "audit_event": "LAYOUT_SAVED"}


@router.post("/data")
def get_dashboard_data(payload: dict):
    filters = payload.get("filters", {})
    if filters.get("branchId") and not filters.get("companyId"):
        raise HTTPException(status_code=422, detail="Branch filter requires company filter")
    dashboard_type = payload.get("dashboardType", "User")
    return {
        "dashboardType": dashboard_type,
        "header_summary_strip": {"open_tasks": 12, "sla_breaches": 3, "pending_approvals": 4},
        "kpi_cards": [{"name": "My Tasks", "value": 12}, {"name": "SLA Alerts", "value": 3}, {"name": "Timesheet Pending", "value": 2}],
        "alerts_panel": [{"type": "SLA", "message": "3 tickets close to breach"}],
        "quick_action_panel": ["Add Task", "Raise Ticket", "Ask Bruno"],
        "bruno_quick_access_panel": ["What should I work on first today?", "Show my overdue tasks"],
        "recent_activity_feed": [{"when": "just now", "event": "Task TSK-441 reassigned"}],
        "filters_applied": filters,
    }


@router.post("/widget/add")
def add_widget(payload: dict):
    role = payload.get("dashboardType", "User")
    widget_name = payload.get("widgetName")
    if not widget_name:
        raise HTTPException(status_code=422, detail="widgetName is required")
    key = f"{role}:{payload.get('userId', 1)}"
    current = LAYOUTS.get(key) or get_dashboard_layout(role=role, user_id=payload.get("userId", 1))
    if widget_name in current["widgets"]:
        raise HTTPException(status_code=409, detail="Duplicate widget not allowed")
    current["widgets"].append(widget_name)
    LAYOUTS[key] = current
    return {"status": "widget_added", "layout": current, "audit_event": "WIDGET_ADDED"}


@router.post("/widget/remove")
def remove_widget(payload: dict):
    role = payload.get("dashboardType", "User")
    widget_name = payload.get("widgetName")
    key = f"{role}:{payload.get('userId', 1)}"
    current = LAYOUTS.get(key) or get_dashboard_layout(role=role, user_id=payload.get("userId", 1))
    if widget_name not in current["widgets"]:
        raise HTTPException(status_code=404, detail="Widget not found in layout")
    current["widgets"] = [w for w in current["widgets"] if w != widget_name]
    LAYOUTS[key] = current
    return {"status": "widget_removed", "layout": current, "audit_event": "WIDGET_REMOVED"}


@router.get("/datasets")
def list_datasets(user_role: str = "Analyst"):
    allowed = [d for d in DATASETS if user_role in d["roles"]]
    return {"datasets": allowed, "rbac_applied": True}


@router.post("/widgets/preview")
def preview_widget(payload: WidgetCreateRequest, user_role: str = "Analyst", scope: str = "SELF"):
    ds = _dataset_by_code(payload.dataset_code)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if user_role not in ds["roles"]:
        raise HTTPException(status_code=403, detail="Dataset not permitted by RBAC")
    if payload.x_axis not in ds["fields"] or payload.y_axis not in ds["fields"]:
        raise HTTPException(status_code=422, detail="Invalid axis field for dataset")

    return {
        "preview": True,
        "chart_type": payload.chart_type,
        "aggregation": payload.aggregation,
        "scope_applied": scope,
        "sample_points": [
            {"x": "A", "y": 10},
            {"x": "B", "y": 18},
            {"x": "C", "y": 13},
        ],
    }


@router.post("/widgets")
def save_widget(payload: WidgetCreateRequest, user_role: str = "Analyst", scope: str = "SELF"):
    preview_widget(payload, user_role=user_role, scope=scope)
    wid = len(WIDGETS) + 1
    WIDGETS[wid] = {
        "widget_id": wid,
        **payload.model_dump(),
        "user_role": user_role,
        "scope": scope,
        "created_at": datetime.utcnow(),
    }
    return WIDGETS[wid]


@router.get("/widgets")
def list_widgets(dashboard_code: str = "DEFAULT"):
    return [w for w in WIDGETS.values() if w["dashboard_code"] == dashboard_code]


@router.put("/widgets/{widget_id}")
def update_widget(widget_id: int, payload: WidgetCreateRequest):
    row = WIDGETS.get(widget_id)
    if not row:
        raise HTTPException(status_code=404, detail="Widget not found")
    row.update(payload.model_dump())
    row["updated_at"] = datetime.utcnow()
    return row


@router.delete("/widgets/{widget_id}")
def delete_widget(widget_id: int):
    if widget_id not in WIDGETS:
        raise HTTPException(status_code=404, detail="Widget not found")
    del WIDGETS[widget_id]
    return {"status": "deleted", "widget_id": widget_id}


@router.get("/reports/usage")
def dashboard_usage_report():
    return {
        "dashboard_usage_report": {"total_widgets": len(WIDGETS), "dashboards": 1},
        "widget_usage_report": [{"widget_id": w["widget_id"], "dataset_code": w["dataset_code"]} for w in WIDGETS.values()],
        "dataset_usage_report": [{"dataset_code": d["dataset_code"], "widget_count": len([w for w in WIDGETS.values() if w["dataset_code"] == d["dataset_code"]])} for d in DATASETS],
    }


@router.get("/analytics/summary")
def dashboard_analytics_summary():
    chart_usage: dict[str, int] = {}
    for row in WIDGETS.values():
        chart_usage[row["chart_type"]] = chart_usage.get(row["chart_type"], 0) + 1

    return {
        "most_used_datasets": sorted(
            [{"dataset": d["dataset_code"], "count": len([w for w in WIDGETS.values() if w["dataset_code"] == d["dataset_code"]])} for d in DATASETS],
            key=lambda x: x["count"],
            reverse=True,
        ),
        "most_used_chart_types": chart_usage,
        "query_performance_tracking": {"p95_ms": 120, "error_rate": 0.0},
    }
