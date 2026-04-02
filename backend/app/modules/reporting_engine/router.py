from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/reports", tags=["Global Reporting Engine"])

REPORT_TEMPLATES = [
    {"code": "COMPANY_LISTING", "module": "MASTERS", "fields": ["company_id", "name", "status"]},
    {"code": "ROLE_PERMISSION_MATRIX", "module": "RBAC", "fields": ["role", "permission", "scope"]},
    {"code": "INTERCONNECT_MATRIX", "module": "INTERCONNECT", "fields": ["source", "target", "coverage"]},
    {"code": "DASHBOARD_USAGE", "module": "DASHBOARD", "fields": ["dashboard", "widget", "usage_count"]},
]

SCHEDULES: dict[int, dict] = {}


class ReportRunRequest(BaseModel):
    report_code: str
    selected_fields: list[str] = Field(default_factory=list)
    filters: dict[str, str | list[str]] = Field(default_factory=dict)
    sort_by: str | None = None
    group_by: str | None = None
    user_role: str = "Analyst"
    scope: str = "SELF"


class ReportExportRequest(ReportRunRequest):
    format: str = "xlsx"


class ReportScheduleRequest(BaseModel):
    report_code: str
    frequency: str
    recipients: list[str]
    format: str = "xlsx"


@router.get("/templates")
def list_templates(module_code: str | None = None):
    rows = REPORT_TEMPLATES
    if module_code:
        rows = [r for r in rows if r["module"] == module_code]
    return rows


@router.post("/run")
def run_report(payload: ReportRunRequest):
    tpl = next((t for t in REPORT_TEMPLATES if t["code"] == payload.report_code), None)
    if not tpl:
        raise HTTPException(status_code=404, detail="Report template not found")

    fields = payload.selected_fields or tpl["fields"]
    if not fields:
        raise HTTPException(status_code=422, detail="At least one field must be selected")

    return {
        "report_code": payload.report_code,
        "fields": fields,
        "rbac_applied": True,
        "scope_applied": payload.scope,
        "row_count": 3,
        "rows": [{f: f"sample_{i}_{f}" for f in fields} for i in range(1, 4)],
    }


@router.post("/export")
def export_report(payload: ReportExportRequest):
    run_report(payload)
    if payload.format.lower() not in {"xlsx", "pdf"}:
        raise HTTPException(status_code=422, detail="Supported formats: xlsx, pdf")

    return {
        "status": "exported",
        "report_code": payload.report_code,
        "format": payload.format.lower(),
        "download_token": f"mock-{payload.report_code.lower()}-{payload.format.lower()}",
        "exported_at": datetime.utcnow(),
    }


@router.get("/schedules")
def list_schedules():
    return list(SCHEDULES.values())


@router.post("/schedules")
def schedule_report(payload: ReportScheduleRequest):
    if payload.frequency.upper() not in {"DAILY", "WEEKLY", "MONTHLY"}:
        raise HTTPException(status_code=422, detail="frequency must be DAILY/WEEKLY/MONTHLY")
    next_id = len(SCHEDULES) + 1
    row = {"schedule_id": next_id, **payload.model_dump(), "created_at": datetime.utcnow(), "status": "ACTIVE"}
    SCHEDULES[next_id] = row
    return row
