from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/system-audit", tags=["System Audit"])

AUDIT_ENTRIES: dict[int, dict] = {}


class AuditCreateRequest(BaseModel):
    user_name: str
    module: str
    reference_id: str
    action_type: str
    field_name: str | None = None
    old_value: Any | None = None
    new_value: Any | None = None
    remarks: str | None = None
    context: dict | None = None


def add_audit_entry(payload: AuditCreateRequest) -> dict:
    next_id = len(AUDIT_ENTRIES) + 1
    row = {
        "audit_id": next_id,
        **payload.model_dump(),
        "timestamp": datetime.utcnow(),
    }
    AUDIT_ENTRIES[next_id] = row
    return row


@router.post("/events")
def create_audit_event(payload: AuditCreateRequest):
    return add_audit_entry(payload)


@router.get("/logs")
def list_audit_logs(
    user_name: str | None = None,
    action_type: str | None = None,
    module: str | None = None,
    reference_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    rows = list(AUDIT_ENTRIES.values())
    if user_name:
        rows = [r for r in rows if r["user_name"] == user_name]
    if action_type:
        rows = [r for r in rows if r["action_type"] == action_type]
    if module:
        rows = [r for r in rows if r["module"] == module]
    if reference_id:
        rows = [r for r in rows if str(r["reference_id"]) == str(reference_id)]
    if date_from:
        rows = [r for r in rows if r["timestamp"] >= date_from]
    if date_to:
        rows = [r for r in rows if r["timestamp"] <= date_to]
    return rows


@router.get("/logs/{audit_id}")
def audit_detail(audit_id: int):
    row = AUDIT_ENTRIES.get(audit_id)
    if not row:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    return {
        "action_summary": {
            "user": row["user_name"],
            "action": row["action_type"],
            "module": row["module"],
            "record_id": row["reference_id"],
            "timestamp": row["timestamp"],
        },
        "field_level_change": {
            "field": row["field_name"],
            "old": row["old_value"],
            "new": row["new_value"],
        },
        "context": row.get("context"),
    }


@router.get("/search")
def search_audit(q: str):
    rows = [
        r
        for r in AUDIT_ENTRIES.values()
        if q.lower() in str(r["user_name"]).lower()
        or q.lower() in str(r["reference_id"]).lower()
        or q.lower() in str(r.get("field_name") or "").lower()
        or q.lower() in str(r.get("old_value") or "").lower()
        or q.lower() in str(r.get("new_value") or "").lower()
    ]
    return rows


@router.get("/reports/summary")
def audit_reports():
    rows = list(AUDIT_ENTRIES.values())
    return {
        "user_activity_report": rows,
        "change_log_report": [r for r in rows if r.get("field_name")],
        "critical_change_report": [r for r in rows if r.get("field_name") in {"status", "end_date", "due_date", "cost"}],
        "rollover_audit": [r for r in rows if r["action_type"] == "ROLLOVER"],
        "approval_audit": [r for r in rows if r["module"] == "APPROVAL"],
    }


@router.get("/analytics/summary")
def audit_analytics():
    rows = list(AUDIT_ENTRIES.values())
    users = sorted({r["user_name"] for r in rows})
    fields = sorted({r["field_name"] for r in rows if r.get("field_name")})
    return {
        "most_active_users": sorted(
            [{"user": u, "events": len([r for r in rows if r["user_name"] == u])} for u in users],
            key=lambda x: x["events"],
            reverse=True,
        ),
        "most_edited_fields": sorted(
            [{"field": f, "edits": len([r for r in rows if r.get("field_name") == f])} for f in fields],
            key=lambda x: x["edits"],
            reverse=True,
        ),
        "frequent_delays": len([r for r in rows if r["action_type"] in {"JOB_DELAYED", "TASK_DELAY", "PROJECT_DELAY"}]),
        "system_misuse_patterns": len([r for r in rows if r["action_type"] == "ADMIN_OVERRIDE"]),
    }


@router.get("/export")
def export_logs(format: str = "excel"):
    if format not in {"excel", "pdf"}:
        raise HTTPException(status_code=422, detail="Unsupported format")
    return {"format": format, "rows": list(AUDIT_ENTRIES.values())}
