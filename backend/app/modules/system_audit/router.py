from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.system_audit.service import audit_service

router = APIRouter(prefix="/system-audit", tags=["System Audit"])
alias_router = APIRouter(prefix="/audit", tags=["System Audit"])


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


class AuditSearchRequest(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    user_name: str | None = None
    role: str | None = None
    module: str | None = None
    screen: str | None = None
    action_type: str | None = None
    reference_id: str | None = None
    q: str | None = None


class AuditExportRequest(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    module: str | None = None
    action_type: str | None = None
    has_privilege: bool = False
    format: str = "excel"


def add_audit_entry(payload: AuditCreateRequest) -> dict:
    return audit_service.add(payload.model_dump())


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
    return audit_service.list(
        user_name=user_name,
        action_type=action_type,
        module=module,
        reference_id=reference_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/logs/{audit_id}")
def audit_detail(audit_id: int):
    return audit_service.detail(audit_id)


@router.get("/search")
def search_audit(q: str):
    return audit_service.search(q)


@router.get("/reports/summary")
def audit_reports():
    return audit_service.reports()


@router.get("/analytics/summary")
def audit_analytics():
    return audit_service.analytics()


@router.get("/export")
def export_logs(format: str = "excel"):
    if format not in {"excel", "pdf"}:
        raise HTTPException(status_code=422, detail="Unsupported format")
    return {"format": format, "rows": audit_service.list()}


@alias_router.get("/logs")
def alias_logs():
    return list_audit_logs()


@alias_router.get("/list")
def audit_list():
    return audit_service.list()


@alias_router.post("/search")
def audit_search(payload: AuditSearchRequest):
    if payload.date_from and payload.date_to and payload.date_from > payload.date_to:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")
    rows = audit_service.list(
        user_name=payload.user_name,
        action_type=payload.action_type,
        module=payload.module,
        reference_id=payload.reference_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    if payload.q:
        q = payload.q.lower()
        rows = [r for r in rows if q in str(r).lower()]
    return {"count": len(rows), "items": rows}


@alias_router.get("/detail/{audit_id}")
def audit_detail_alias(audit_id: int):
    return audit_service.detail(audit_id)


@alias_router.post("/export")
def audit_export(payload: AuditExportRequest):
    if not payload.has_privilege:
        raise HTTPException(status_code=403, detail="Export requires privilege")
    if payload.format not in {"excel", "pdf", "csv"}:
        raise HTTPException(status_code=422, detail="Unsupported format")
    rows = audit_service.list(
        action_type=payload.action_type,
        module=payload.module,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    return {"exported_rows": len(rows), "format": payload.format, "watermark": "COMPLIANCE_EXPORT"}
