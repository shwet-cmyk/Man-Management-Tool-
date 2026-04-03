from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/timesheet", tags=["Timesheet"])
TIMESHEETS: dict[int, dict] = {}


class TimesheetEntryRequest(BaseModel):
    entry_date: str
    user: str
    project: str
    task: str | None = None
    job: str | None = None
    hours_logged: float = Field(gt=0)
    billable: bool
    activity_description: str | None = None
    remarks: str | None = None


@router.get("/list")
def list_timesheets(user: str | None = None, project: str | None = None, approval_status: str | None = None):
    rows = list(TIMESHEETS.values())
    if user:
        rows = [r for r in rows if r["user"] == user]
    if project:
        rows = [r for r in rows if r["project"] == project]
    if approval_status:
        rows = [r for r in rows if r["approval_status"] == approval_status]
    return {"count": len(rows), "items": rows}


@router.post("/create")
def create_timesheet(payload: TimesheetEntryRequest):
    next_id = len(TIMESHEETS) + 1
    row = {
        "id": next_id,
        "timesheet_no": f"TS-{datetime.now(UTC).year}-{next_id:05d}",
        **payload.model_dump(),
        "approval_status": "DRAFT",
        "submitted_on": None,
        "approved_by": None,
        "created_at": datetime.now(UTC).isoformat(),
    }
    TIMESHEETS[next_id] = row
    return row


@router.put("/update/{entry_id}")
def update_timesheet(entry_id: int, payload: TimesheetEntryRequest):
    row = TIMESHEETS.get(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    if row["approval_status"] == "APPROVED":
        raise HTTPException(status_code=422, detail="Edit blocked after approval unless reopen process exists")
    row.update(payload.model_dump())
    return row


@router.post("/submit/{entry_id}")
def submit_timesheet(entry_id: int):
    row = TIMESHEETS.get(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    row["approval_status"] = "SUBMITTED"
    row["submitted_on"] = datetime.now(UTC).isoformat()
    return row


@router.post("/withdraw/{entry_id}")
def withdraw_timesheet(entry_id: int):
    row = TIMESHEETS.get(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    if row["approval_status"] == "APPROVED":
        raise HTTPException(status_code=422, detail="Withdraw allowed only before approval")
    row["approval_status"] = "DRAFT"
    return row


@router.post("/approve/{entry_id}")
def approve_timesheet(entry_id: int, approver: str):
    row = TIMESHEETS.get(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    row["approval_status"] = "APPROVED"
    row["approved_by"] = approver
    return row


@router.post("/reject/{entry_id}")
def reject_timesheet(entry_id: int, remarks: str):
    if not remarks.strip():
        raise HTTPException(status_code=422, detail="Rejection remarks mandatory")
    row = TIMESHEETS.get(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    row["approval_status"] = "REJECTED"
    row["remarks"] = remarks
    return row


@router.post("/entry/create")
def create_timesheet_entry(payload: TimesheetEntryRequest):
    return create_timesheet(payload)


@router.put("/entry/update/{entry_id}")
def update_timesheet_entry(entry_id: int, payload: TimesheetEntryRequest):
    return update_timesheet(entry_id, payload)


@router.post("/entry/submit/{entry_id}")
def submit_timesheet_entry(entry_id: int):
    return submit_timesheet(entry_id)


@router.post("/entry/attach/{entry_id}")
def attach_timesheet_entry(entry_id: int, attachment: str):
    row = TIMESHEETS.get(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    row.setdefault("attachments", []).append(attachment)
    return row
