from __future__ import annotations

from datetime import date, datetime, time, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/calendar-intelligence", tags=["Algorithm + Calendar Intelligence"])


class EntryType(str, Enum):
    task = "TASK"
    job = "JOB"
    timesheet = "TIMESHEET"
    meeting = "MEETING"


class CalendarEntryRequest(BaseModel):
    employee: str
    entry_type: EntryType
    reference_id: int
    title: str
    project: str | None = None
    entry_date: date
    start_time: time
    end_time: time
    color: str | None = None


CALENDAR_ENTRIES: dict[int, dict] = {}
SCHEDULING_AUDIT: list[dict] = []
WORKING_HOURS_START = time(9, 0)
WORKING_HOURS_END = time(18, 0)


def _log(event: str, payload: dict):
    SCHEDULING_AUDIT.append({"event": event, "at": datetime.utcnow(), **payload})


def _find_conflicts(employee: str, entry_date: date, start_time: time, end_time: time):
    conflicts = []
    for row in CALENDAR_ENTRIES.values():
        if row["employee"] != employee or row["entry_date"] != entry_date:
            continue
        if start_time < row["end_time"] and end_time > row["start_time"]:
            conflicts.append(row)
    return conflicts


@router.post("/entries")
def create_calendar_entry(payload: CalendarEntryRequest):
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=422, detail="Start must be before end")
    if payload.start_time < WORKING_HOURS_START or payload.end_time > WORKING_HOURS_END:
        raise HTTPException(status_code=422, detail="Outside working hours")

    conflicts = _find_conflicts(payload.employee, payload.entry_date, payload.start_time, payload.end_time)
    if conflicts:
        _log("ENTRY_BLOCKED_CONFLICT", {"employee": payload.employee, "reference_id": payload.reference_id})
        suggestions = suggest_next_available_slot(payload.employee, payload.entry_date, duration_minutes=int((datetime.combine(payload.entry_date, payload.end_time)-datetime.combine(payload.entry_date, payload.start_time)).total_seconds()//60))
        raise HTTPException(
            status_code=409,
            detail={
                "message": "This time slot is already allocated to another task/job.",
                "conflicts": [
                    {
                        "reference_id": c["reference_id"],
                        "title": c["title"],
                        "project": c["project"],
                        "start_time": c["start_time"],
                        "end_time": c["end_time"],
                    }
                    for c in conflicts
                ],
                "actions": [
                    "Go to Conflicting Task",
                    "Reschedule This Task",
                    "Find Next Available Slot",
                ],
                "suggested_slot": suggestions,
            },
        )

    next_id = len(CALENDAR_ENTRIES) + 1
    row = {"entry_id": next_id, **payload.model_dump()}
    if not row["color"]:
        row["color"] = {
            EntryType.task: "BLUE",
            EntryType.job: "GREEN",
            EntryType.meeting: "PURPLE",
            EntryType.timesheet: "ORANGE",
        }[payload.entry_type]
    CALENDAR_ENTRIES[next_id] = row
    _log("ENTRY_CREATED", {"entry_id": next_id, "employee": payload.employee, "entry_type": payload.entry_type})
    return row


@router.get("/entries")
def list_calendar_entries(employee: str | None = None, view: str = "DAY", for_date: date | None = None):
    rows = list(CALENDAR_ENTRIES.values())
    if employee:
        rows = [r for r in rows if r["employee"] == employee]
    if for_date:
        rows = [r for r in rows if r["entry_date"] == for_date]
    return {"view": view, "rows": rows}


@router.post("/validate-conflict")
def validate_conflict(payload: CalendarEntryRequest):
    conflicts = _find_conflicts(payload.employee, payload.entry_date, payload.start_time, payload.end_time)
    return {
        "has_conflict": bool(conflicts),
        "conflicts": conflicts,
    }


@router.get("/suggestions/next-slot")
def suggest_next_available_slot(employee: str, entry_date: date, duration_minutes: int = 60):
    entries = sorted(
        [e for e in CALENDAR_ENTRIES.values() if e["employee"] == employee and e["entry_date"] == entry_date],
        key=lambda x: x["start_time"],
    )

    cursor = datetime.combine(entry_date, WORKING_HOURS_START)
    end_of_day = datetime.combine(entry_date, WORKING_HOURS_END)
    needed = timedelta(minutes=duration_minutes)

    for entry in entries:
        start = datetime.combine(entry_date, entry["start_time"])
        if start - cursor >= needed:
            return {
                "start_time": cursor.time(),
                "end_time": (cursor + needed).time(),
            }
        cursor = max(cursor, datetime.combine(entry_date, entry["end_time"]))

    if end_of_day - cursor >= needed:
        return {"start_time": cursor.time(), "end_time": (cursor + needed).time()}

    return {"message": "No slot available in working hours"}


@router.get("/dashboard")
def employee_calendar_dashboard(employee: str, view: str = "DAY"):
    rows = [r for r in CALENDAR_ENTRIES.values() if r["employee"] == employee]
    return {
        "employee": employee,
        "view": view,
        "events": rows,
        "stats": {
            "total_events": len(rows),
            "tasks": len([r for r in rows if r["entry_type"] == EntryType.task]),
            "jobs": len([r for r in rows if r["entry_type"] == EntryType.job]),
            "meetings": len([r for r in rows if r["entry_type"] == EntryType.meeting]),
            "sla_risk": len([r for r in rows if r["color"] == "ORANGE"]),
            "delayed": len([r for r in rows if r["color"] == "RED"]),
        },
    }


@router.get("/reports/summary")
def scheduling_reports():
    return {
        "employee_utilization_calendar": [
            {
                "employee": emp,
                "entries": len([e for e in CALENDAR_ENTRIES.values() if e["employee"] == emp]),
            }
            for emp in sorted({e["employee"] for e in CALENDAR_ENTRIES.values()})
        ],
        "overbooking_attempts": [a for a in SCHEDULING_AUDIT if a["event"] == "ENTRY_BLOCKED_CONFLICT"],
        "scheduling_efficiency": {"scheduled_entries": len(CALENDAR_ENTRIES)},
    }


@router.get("/analytics/summary")
def scheduling_analytics():
    total = len(CALENDAR_ENTRIES)
    booked_minutes = 0
    for e in CALENDAR_ENTRIES.values():
        booked_minutes += int((datetime.combine(e["entry_date"], e["end_time"]) - datetime.combine(e["entry_date"], e["start_time"])).total_seconds() // 60)
    return {
        "idle_vs_booked": {"booked_minutes": booked_minutes, "idle_minutes_estimate": max(0, total * 540 - booked_minutes)},
        "overbooking_frequency": len([a for a in SCHEDULING_AUDIT if a["event"] == "ENTRY_BLOCKED_CONFLICT"]),
        "scheduling_conflicts": len([a for a in SCHEDULING_AUDIT if a["event"] == "ENTRY_BLOCKED_CONFLICT"]),
    }


@router.get("/audit-log")
def scheduling_audit_log():
    return SCHEDULING_AUDIT
