from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.devlogs.bll import DevlogsBLL
from app.modules.devlogs.dal import DevlogsDAL

router = APIRouter(prefix="/devlogs", tags=["Developer Logs and Metrics"])
_bll = DevlogsBLL(DevlogsDAL())


class DevlogSearchRequest(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    module: str | None = None
    severity: str | None = None
    event_type: str | None = None
    screen: str | None = None
    api: str | None = None
    release_version: str | None = None
    environment: str | None = None
    status: str | None = None
    correlation_id: str | None = None


class DevlogLinkTicketRequest(BaseModel):
    ticket_ref: str = Field(min_length=3)
    linked_by: str


class DevlogNotesRequest(BaseModel):
    note: str = Field(min_length=3)
    added_by: str


@router.get("/dashboard")
def devlogs_dashboard():
    return _bll.dashboard()


@router.post("/search")
def devlogs_search(payload: DevlogSearchRequest):
    if payload.date_from and payload.date_to and payload.date_from > payload.date_to:
        raise HTTPException(status_code=422, detail="date_from must be <= date_to")
    rows = _bll.filter(payload.model_dump())
    return {"count": len(rows), "records": rows}


@router.get("/detail/{item_id}")
def devlogs_detail(item_id: int):
    row = _bll.dal.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Log not found")

    return {
        "event_header": {k: row[k] for k in ["id", "timestamp", "module", "severity", "correlation_id", "release_version", "status"]},
        "message": row["message"],
        "stack_trace": row["stack_trace"],
        "request_payload": row["request_payload"],
        "response_payload": row["response_payload"],
        "related_context": {"surface": row["surface"], "user_context": row["user_context"], "ticket_ref": row["ticket_ref"]},
        "trace_path": ["UI", "API", "DB"],
        "notes": row["notes"],
    }


@router.post("/mark-investigating/{item_id}")
def mark_investigating(item_id: int):
    row = _bll.dal.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Log not found")
    row["status"] = "Investigating"
    return {"success": True, "id": item_id, "status": row["status"]}


@router.post("/mark-resolved/{item_id}")
def mark_resolved(item_id: int):
    row = _bll.dal.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Log not found")
    row["status"] = "Resolved"
    return {"success": True, "id": item_id, "status": row["status"]}


@router.post("/link-ticket/{item_id}")
def link_ticket(item_id: int, payload: DevlogLinkTicketRequest):
    row = _bll.dal.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Log not found")
    row["ticket_ref"] = payload.ticket_ref
    return {"success": True, "id": item_id, "ticket_ref": payload.ticket_ref, "linked_by": payload.linked_by}


@router.post("/notes/{item_id}")
def add_note(item_id: int, payload: DevlogNotesRequest):
    row = _bll.dal.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Log not found")
    _bll.add_note(row, payload.note, payload.added_by)
    return {"success": True, "id": item_id, "notes_count": len(row["notes"])}
