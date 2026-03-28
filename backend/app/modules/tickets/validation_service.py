from __future__ import annotations

from fastapi import HTTPException


ALLOWED_STATUSES = {
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
    "WAITING_FOR_CUSTOMER",
    "WAITING_FOR_INTERNAL_TEAM",
    "RESOLVED",
    "CLOSED",
    "REOPENED",
    "ESCALATED",
}

ALLOWED_TRANSITIONS = {
    "OPEN": {"ASSIGNED", "IN_PROGRESS", "ESCALATED", "CLOSED"},
    "ASSIGNED": {"IN_PROGRESS", "WAITING_FOR_INTERNAL_TEAM", "ESCALATED", "CLOSED"},
    "IN_PROGRESS": {"WAITING_FOR_CUSTOMER", "WAITING_FOR_INTERNAL_TEAM", "RESOLVED", "ESCALATED"},
    "WAITING_FOR_CUSTOMER": {"IN_PROGRESS", "ESCALATED", "CLOSED"},
    "WAITING_FOR_INTERNAL_TEAM": {"IN_PROGRESS", "ESCALATED", "CLOSED"},
    "RESOLVED": {"CLOSED", "REOPENED", "ESCALATED"},
    "CLOSED": {"REOPENED"},
    "REOPENED": {"ASSIGNED", "IN_PROGRESS", "ESCALATED", "CLOSED"},
    "ESCALATED": {"IN_PROGRESS", "WAITING_FOR_CUSTOMER", "WAITING_FOR_INTERNAL_TEAM", "RESOLVED", "CLOSED"},
}


class ValidationService:
    def validate_priority(self, priority: str):
        if priority.upper() not in {"HIGH", "MEDIUM", "LOW"}:
            raise HTTPException(status_code=422, detail="Priority must be High/Medium/Low")

    def validate_transition(self, current: str, target: str):
        current_u = current.upper()
        target_u = target.upper()
        if target_u not in ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail="Invalid target status")
        if target_u not in ALLOWED_TRANSITIONS.get(current_u, set()):
            raise HTTPException(status_code=422, detail=f"Invalid status transition: {current} -> {target}")

    def validate_first_response_note(self, note: str | None):
        if not note or len(note.strip()) < 3:
            raise HTTPException(status_code=422, detail="Valid first response requires meaningful note")

    def validate_waiting_transition(self, target: str, pause_reason: str | None):
        if target.upper() in {"WAITING_FOR_CUSTOMER", "WAITING_FOR_INTERNAL_TEAM"} and not pause_reason:
            raise HTTPException(status_code=422, detail="Waiting statuses require pause reason")

    def validate_closure(self, target: str, resolution_note: str | None):
        if target.upper() == "CLOSED" and not (resolution_note and resolution_note.strip()):
            raise HTTPException(status_code=422, detail="Close requires closure remark")

    def validate_rollover(self, previous_due_at, revised_due_at, reason: str):
        if revised_due_at <= previous_due_at:
            raise HTTPException(status_code=422, detail="Rollover requires later due date")
        if not reason.strip():
            raise HTTPException(status_code=422, detail="Rollover reason is required")
