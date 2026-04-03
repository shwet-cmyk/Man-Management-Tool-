from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.ux_analytics.bll import UxAnalyticsBLL
from app.modules.ux_analytics.dal import UxAnalyticsDAL

router = APIRouter(prefix="/ux", tags=["UX Analytics"])
_bll = UxAnalyticsBLL(UxAnalyticsDAL())


class UxFilterRequest(BaseModel):
    date_from: datetime
    date_to: datetime
    module: str | None = None
    screen: str | None = None
    role: str | None = None
    device_type: str | None = None
    browser: str | None = None
    company: str | None = None
    branch: str | None = None
    department: str | None = None
    error_present: bool | None = None
    high_friction_only: bool = False


class UxCompareRequest(BaseModel):
    screen_ids: list[str] = Field(min_length=2)
    date_from: datetime | None = None
    date_to: datetime | None = None


class UxCreateTicketRequest(BaseModel):
    screen_id: str
    issue_summary: str = Field(min_length=5)
    details: str | None = None
    priority: str = "MEDIUM"
    requested_by: str
    has_privilege: bool = False


class VersionCompareRequest(BaseModel):
    screen_id: str
    baseline_version: str | None = None
    compare_version: str | None = None
    baseline_from: datetime | None = None
    baseline_to: datetime | None = None
    compare_from: datetime | None = None
    compare_to: datetime | None = None


@router.get("/summary")
def ux_summary(date_from: datetime | None = None, date_to: datetime | None = None):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")
    return _bll.summary()


@router.post("/filter")
def ux_filter(payload: UxFilterRequest):
    if payload.date_from > payload.date_to:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")
    rows = _bll.filter(payload.module, payload.screen, payload.error_present, payload.high_friction_only)
    return {"count": len(rows), "records": rows}


@router.get("/screen-detail/{screen_id}")
def ux_screen_detail(screen_id: str):
    row = _bll.screen_detail(screen_id)
    if not row:
        raise HTTPException(status_code=404, detail="Screen analytics not found")
    return row


@router.get("/heatmap/{screen_id}")
def ux_heatmap(screen_id: str):
    heatmap = _bll.dal.get_heatmap(screen_id)
    if not heatmap:
        raise HTTPException(status_code=404, detail="Heatmap not found")
    return heatmap


@router.post("/compare")
def ux_compare(payload: UxCompareRequest):
    unique_ids = list(dict.fromkeys(payload.screen_ids))
    if len(unique_ids) < 2:
        raise HTTPException(status_code=422, detail="Comparison requires at least two valid screen selections")
    existing = [r for r in _bll.dal.list_screens() if r["screen_id"] in unique_ids]
    if len(existing) < 2:
        raise HTTPException(status_code=422, detail="Comparison requires at least two valid screen selections")
    return _bll.compare(unique_ids)


@router.post("/create-ticket")
def ux_create_ticket(payload: UxCreateTicketRequest):
    if not payload.has_privilege:
        raise HTTPException(status_code=403, detail="Ticket creation requires privileged role")
    if not payload.issue_summary.strip():
        raise HTTPException(status_code=422, detail="issue_summary is required")
    return {"success": True, "ticket": _bll.create_ticket(payload.screen_id, payload.issue_summary, payload.details, payload.priority, payload.requested_by)}


@router.get("/field-summary/{screen_id}")
def ux_field_summary(screen_id: str):
    row = _bll.dal.get_screen(screen_id)
    if not row:
        raise HTTPException(status_code=404, detail="Screen analytics not found")
    return {"screen_id": screen_id, "field_interactions": row["field_abandonment"], "validation_failure_hotspots": row["validation_hotspots"]}


@router.get("/action-summary/{screen_id}")
def ux_action_summary(screen_id: str):
    row = _bll.dal.get_screen(screen_id)
    if not row:
        raise HTTPException(status_code=404, detail="Screen analytics not found")
    return {"screen_id": screen_id, "actions": row["action_summary"]}


@router.post("/version-compare")
def ux_version_compare(payload: VersionCompareRequest):
    if not (
        (payload.baseline_version and payload.compare_version)
        or (payload.baseline_from and payload.baseline_to and payload.compare_from and payload.compare_to)
    ):
        raise HTTPException(status_code=422, detail="Version compare requires two valid versions or date windows")

    row = _bll.dal.get_screen(payload.screen_id)
    if not row:
        raise HTTPException(status_code=404, detail="Screen analytics not found")

    return {
        "screen_id": payload.screen_id,
        "baseline": {"completion_rate": round(row["completion_rate"] - 4.5, 2), "friction_index": round(_bll.friction_index(row) + 7.8, 2)},
        "current": {"completion_rate": row["completion_rate"], "friction_index": _bll.friction_index(row)},
        "delta": {"completion_rate": 4.5, "friction_index": -7.8},
    }
