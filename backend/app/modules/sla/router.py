from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.modules.approval.router import APPROVALS
from app.modules.tasks.router import TASKS
from app.modules.tickets.router import TICKETS

router = APIRouter(prefix="/sla", tags=["SLA Monitor"])
SLA_ACTION_AUDIT: list[dict] = []


def _now():
    return datetime.now(UTC)


def _build_rows() -> list[dict]:
    rows: list[dict] = []
    for task in TASKS.values():
        due = task.get("sla_due_at")
        rows.append({
            "record_type": "TASK",
            "record_id": task["task_id"],
            "reference_no": f"TSK-{task['task_id']}",
            "title": task["task_name"],
            "priority": task["priority"],
            "current_status": task["status"],
            "owner": task.get("task_owner"),
            "start_time": task.get("sla_started_at"),
            "due_time": due,
            "time_remaining_seconds": int((due - datetime.utcnow()).total_seconds()) if due else None,
            "sla_state": "BREACHED" if due and datetime.utcnow() > due else "RUNNING",
            "escalation_level": task.get("escalation_level", 0),
        })
    for ticket in TICKETS.values():
        due = ticket.get("sla_due_at")
        rows.append({
            "record_type": "TICKET",
            "record_id": ticket["ticket_id"],
            "reference_no": ticket["ticket_no"],
            "title": ticket["remark"],
            "priority": ticket["priority"],
            "current_status": ticket["status"],
            "owner": ticket.get("executive_name"),
            "start_time": ticket.get("sla_started_at"),
            "due_time": due,
            "time_remaining_seconds": int((due - datetime.utcnow()).total_seconds()) if due else None,
            "sla_state": ticket.get("sla_state", "RUNNING"),
            "escalation_level": ticket.get("escalation_level", 0),
        })
    for approval in APPROVALS.values():
        due = approval["created_at"]
        rows.append({
            "record_type": "APPROVAL",
            "record_id": approval["approval_id"],
            "reference_no": f"APR-{approval['approval_id']}",
            "title": f"Approval {approval['module']}",
            "priority": approval.get("priority", "MEDIUM"),
            "current_status": approval["state"],
            "owner": approval.get("level1_approver_user_id"),
            "start_time": approval.get("created_at"),
            "due_time": due,
            "time_remaining_seconds": int((due - datetime.utcnow()).total_seconds()),
            "sla_state": "BREACHED" if approval.get("escalated") else "RUNNING",
            "escalation_level": 1 if approval.get("escalated") else 0,
        })
    return rows


@router.get("/list")
def sla_list(record_type: str | None = None, priority: str | None = None, sla_state: str | None = None, assignee: str | None = None):
    rows = _build_rows()
    if record_type:
        rows = [r for r in rows if r["record_type"] == record_type.upper()]
    if priority:
        rows = [r for r in rows if str(r["priority"]).upper() == priority.upper()]
    if sla_state:
        rows = [r for r in rows if str(r["sla_state"]).upper() == sla_state.upper()]
    if assignee:
        rows = [r for r in rows if str(r["owner"]) == assignee]
    return {"count": len(rows), "items": rows}


@router.post("/search")
def sla_search(payload: dict):
    data = sla_list(record_type=payload.get("recordType"), priority=payload.get("priority"), sla_state=payload.get("slaState"), assignee=payload.get("assignee"))
    q = payload.get("query")
    if q:
        q_low = q.lower()
        data["items"] = [r for r in data["items"] if q_low in r["reference_no"].lower() or q_low in str(r["title"]).lower()]
        data["count"] = len(data["items"])
    return data


def _find(record_id: int):
    if record_id in TASKS:
        return "TASK", TASKS[record_id]
    if record_id in TICKETS:
        return "TICKET", TICKETS[record_id]
    if record_id in APPROVALS:
        return "APPROVAL", APPROVALS[record_id]
    raise HTTPException(status_code=404, detail="Record not found")


@router.post("/escalate/{record_id}")
def escalate_record(record_id: int):
    module, row = _find(record_id)
    row["escalation_level"] = row.get("escalation_level", 0) + 1
    row["escalated"] = True
    SLA_ACTION_AUDIT.append({"event": "SLA_ESCALATED", "module": module, "record_id": record_id, "at": _now()})
    return {"status": "escalated", "record_id": record_id, "module": module, "escalation_level": row["escalation_level"]}


@router.post("/pause/{record_id}")
def pause_record(record_id: int):
    module, row = _find(record_id)
    if module == "APPROVAL":
        raise HTTPException(status_code=422, detail="Pause not allowed for this record type")
    row["sla_state"] = "PAUSED"
    SLA_ACTION_AUDIT.append({"event": "SLA_PAUSED", "module": module, "record_id": record_id, "at": _now()})
    return {"status": "paused", "record_id": record_id, "module": module}


@router.post("/reassign/{record_id}")
def reassign_record(record_id: int, new_owner: str):
    module, row = _find(record_id)
    if module == "TASK":
        row["task_owner"] = new_owner
    elif module == "TICKET":
        row["executive_name"] = new_owner
    else:
        row["level1_approver_user_id"] = int(new_owner) if str(new_owner).isdigit() else new_owner
    SLA_ACTION_AUDIT.append({"event": "SLA_REASSIGNED", "module": module, "record_id": record_id, "new_owner": new_owner, "at": _now()})
    return {"status": "reassigned", "record_id": record_id, "module": module, "new_owner": new_owner}
