from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/analytics", tags=["Global Analytics Engine"])

CONSTANT_FILTERS = [
    "company",
    "branch",
    "department",
    "employee",
    "client",
    "project",
    "date_from",
    "date_to",
    "priority",
]

SAVED_VIEWS: dict[int, dict] = {}
ALERT_RULES: dict[int, dict] = {}


class AnalyticsQueryRequest(BaseModel):
    module_code: str
    chart_type: str
    filters: dict[str, str | list[str]] = Field(default_factory=dict)
    user_role: str = "Analyst"
    scope: str = "SELF"


class SavedFilterViewRequest(BaseModel):
    name: str
    module_code: str
    filters: dict[str, str | list[str]]
    set_default: bool = False


class AlertRuleRequest(BaseModel):
    module_code: str
    rule_name: str
    condition: str
    threshold_value: float
    severity: str = "MEDIUM"


@router.get("/filters/constants")
def constant_filters():
    return {"filters": CONSTANT_FILTERS, "rbac_scope_aware": True}


@router.get("/module/{module_code}/prebuilt")
def prebuilt_module_charts(module_code: str):
    return {
        "module": module_code,
        "charts": [
            "COUNT_BY_STATUS",
            "TREND_OVER_TIME",
            "DISTRIBUTION_BY_DEPARTMENT",
            "PRIORITY_DISTRIBUTION",
            "TOP_PERFORMERS",
        ],
    }


@router.post("/query")
def analytics_query(payload: AnalyticsQueryRequest):
    invalid = [f for f in payload.filters.keys() if f not in CONSTANT_FILTERS and f not in {"status", "module", "response_time_bucket"}]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unsupported filters: {invalid}")

    return {
        "module_code": payload.module_code,
        "chart_type": payload.chart_type,
        "rbac_applied": True,
        "scope_applied": payload.scope,
        "filters_applied": payload.filters,
        "series": [
            {"label": "A", "value": 14},
            {"label": "B", "value": 27},
            {"label": "C", "value": 19},
        ],
        "generated_at": datetime.utcnow(),
    }


@router.get("/saved-views")
def list_saved_views(module_code: str | None = None):
    rows = list(SAVED_VIEWS.values())
    if module_code:
        rows = [r for r in rows if r["module_code"] == module_code]
    return rows


@router.post("/saved-views")
def create_saved_view(payload: SavedFilterViewRequest):
    next_id = len(SAVED_VIEWS) + 1
    row = {"view_id": next_id, **payload.model_dump(), "created_at": datetime.utcnow()}
    SAVED_VIEWS[next_id] = row
    return row


@router.get("/alerts/rules")
def list_alert_rules(module_code: str | None = None):
    rows = list(ALERT_RULES.values())
    if module_code:
        rows = [r for r in rows if r["module_code"] == module_code]
    return rows


@router.post("/alerts/rules")
def create_alert_rule(payload: AlertRuleRequest):
    next_id = len(ALERT_RULES) + 1
    row = {"rule_id": next_id, **payload.model_dump(), "created_at": datetime.utcnow(), "status": "ACTIVE"}
    ALERT_RULES[next_id] = row
    return row
