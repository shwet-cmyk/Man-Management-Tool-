from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.status_engine.router import ModuleType, PriorityType, validate_status_transition

router = APIRouter(prefix="/tickets", tags=["Ticket Module"])


class TicketType(str, Enum):
    amc = "AMC"
    support = "SUPPORT"
    installation = "INSTALLATION"
    enhancement = "ENHANCEMENT"


class TicketCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_name: str = Field(..., min_length=2)
    remark: str = Field(..., min_length=3)
    category: str = Field(..., min_length=2)
    ticket_type: TicketType
    priority: PriorityType
    executive_name: str = Field(..., min_length=2)
    executive_email: str | None = None
    showstopper: bool = False
    attachment: str | None = None

    mobile: str | None = None
    contact_person: str | None = None
    email: str | None = None
    address: str | None = None
    erp_id: str | None = None
    pack_validity: str | None = None
    sms_balance: float | None = None
    whatsapp_balance: float | None = None
    username: str | None = None
    max_users: int | None = None


class TicketUpdateRequest(BaseModel):
    customer_name: str | None = None
    product_name: str | None = None
    remark: str | None = None
    category: str | None = None
    priority: PriorityType | None = None
    executive_name: str | None = None
    attachment: str | None = None


class TicketStatusUpdateRequest(BaseModel):
    status: str
    actor: str
    actor_role: str
    remark: str | None = None
    approval_granted: bool = False


class FollowupCreateRequest(BaseModel):
    followup_type: str = Field(..., min_length=2)
    remark: str = Field(..., min_length=2)
    status: str
    executive_name: str = Field(..., min_length=2)
    attachment: str | None = None
    ticket_charges: bool = False
    amount_collected: float | None = None
    travelling_expenses: float | None = None


TICKETS: dict[int, dict] = {}
FOLLOWUPS: dict[int, list[dict]] = {}
TICKET_AUDIT: list[dict] = []
NOTIFICATIONS: list[dict] = []


def _log(event: str, payload: dict):
    TICKET_AUDIT.append({"event": event, "at": datetime.utcnow(), **payload})


def _sla_due_at(priority: PriorityType, showstopper: bool, at: datetime) -> datetime:
    if showstopper:
        return at + timedelta(hours=24)
    days = 7 if priority == PriorityType.low else 3
    return at + timedelta(days=days)


def _sla_indicator(ticket: dict) -> str:
    if ticket["sla_state"] == "BREACHED":
        return "BREACHED"
    now = datetime.utcnow()
    due = ticket["sla_due_at"]
    warning_threshold = due - timedelta(days=1)
    if now >= due:
        return "BREACHED"
    if now >= warning_threshold:
        return "WARNING"
    return "ON_TRACK"


@router.get("")
def list_tickets(
    status: str | None = None,
    ticket_no: str | None = None,
    executive: str | None = None,
    category: str | None = None,
    customer: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    rows = list(TICKETS.values())
    if status and status != "ALL":
        rows = [r for r in rows if r["status"] == status]
    if ticket_no:
        rows = [r for r in rows if r["ticket_no"] == ticket_no]
    if executive:
        rows = [r for r in rows if r["executive_name"] == executive]
    if category:
        rows = [r for r in rows if r["category"] == category]
    if customer:
        rows = [r for r in rows if r["customer_name"] == customer]
    if date_from:
        rows = [r for r in rows if r["created_at"] >= date_from]
    if date_to:
        rows = [r for r in rows if r["created_at"] <= date_to]

    enriched = []
    for row in rows:
        item = {**row}
        item["tat_seconds_left"] = max(0, int((row["sla_due_at"] - datetime.utcnow()).total_seconds()))
        item["sla_indicator"] = _sla_indicator(row)
        enriched.append(item)
    return enriched


@router.get("/list")
def list_tickets_contract(status: str | None = None, priority: PriorityType | None = None, assigned_to: str | None = None):
    rows = list_tickets(status=status, executive=assigned_to)
    if priority:
        rows = [r for r in rows if r["priority"] == priority]
    return {"count": len(rows), "items": rows}


@router.post("/search")
def search_tickets(payload: dict):
    rows = list_tickets_contract(
        status=payload.get("status"),
        priority=payload.get("priority"),
        assigned_to=payload.get("assignedTo"),
    )
    q = payload.get("query")
    if q:
        q_low = q.lower()
        rows["items"] = [r for r in rows["items"] if q_low in r["ticket_no"].lower() or q_low in r["remark"].lower()]
        rows["count"] = len(rows["items"])
    return rows


@router.post("")
def create_ticket(payload: TicketCreateRequest):
    created_at = datetime.utcnow()
    next_id = len(TICKETS) + 1

    ticket = {
        "ticket_id": next_id,
        "ticket_no": f"TKT-{created_at.year}-{next_id:05d}",
        **payload.model_dump(),
        "status": "OPEN",
        "created_at": created_at,
        "updated_at": created_at,
        "sla_started_at": created_at,
        "sla_due_at": _sla_due_at(payload.priority, payload.showstopper, created_at),
        "sla_state": "RUNNING",
        "total_effort_minutes": 0,
    }
    TICKETS[next_id] = ticket
    FOLLOWUPS[next_id] = []

    _log("TICKET_CREATED", {"ticket_id": next_id, "status": "OPEN", "priority": payload.priority})
    NOTIFICATIONS.append(
        {
            "event": "TICKET_CREATED",
            "ticket_id": next_id,
            "to": payload.executive_name,
            "message": "New ticket assigned",
            "at": datetime.utcnow(),
        }
    )

    return ticket


@router.post("/create")
def create_ticket_contract(payload: TicketCreateRequest):
    return create_ticket(payload)


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {**row, "followups": FOLLOWUPS.get(ticket_id, [])}


@router.put("/{ticket_id}")
def update_ticket(ticket_id: int, payload: TicketUpdateRequest):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")

    updates = payload.model_dump(exclude_none=True)
    if "priority" in updates:
        row["sla_due_at"] = _sla_due_at(updates["priority"], row["showstopper"], row["sla_started_at"])
    row.update(updates)
    row["updated_at"] = datetime.utcnow()
    _log("TICKET_UPDATED", {"ticket_id": ticket_id, "fields": sorted(updates.keys())})
    return row


@router.put("/update/{ticket_id}")
def update_ticket_contract(ticket_id: int, payload: TicketUpdateRequest):
    return update_ticket(ticket_id, payload)


@router.patch("/{ticket_id}/status")
def update_ticket_status(ticket_id: int, payload: TicketStatusUpdateRequest):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if payload.status == "CLOSED" and not FOLLOWUPS.get(ticket_id):
        raise HTTPException(status_code=422, detail="Development to Closed requires at least one followup")

    transition_data = validate_status_transition(
        module=ModuleType.ticket,
        from_status=row["status"],
        to_status=payload.status,
        actor_role=payload.actor_role,
        approval_granted=payload.approval_granted,
    )
    transition = transition_data["transition"]
    next_status = transition_data["next_status_def"]

    if next_status["pause_sla"]:
        row["sla_state"] = "PAUSED"
        row["sla_paused_at"] = datetime.utcnow()
    elif next_status["resume_sla"] and row.get("sla_paused_at"):
        pause_elapsed = datetime.utcnow() - row["sla_paused_at"]
        row["sla_due_at"] = row["sla_due_at"] + pause_elapsed
        row["sla_paused_at"] = None
        row["sla_state"] = "RUNNING"

    if datetime.utcnow() > row["sla_due_at"] and payload.status != "CLOSED":
        row["sla_state"] = "BREACHED"

    old = row["status"]
    row["status"] = payload.status
    row["updated_at"] = datetime.utcnow()

    _log(
        "TICKET_STATUS_CHANGED",
        {
            "ticket_id": ticket_id,
            "from": old,
            "to": payload.status,
            "actor": payload.actor,
            "actor_role": payload.actor_role,
            "remark": payload.remark,
        },
    )
    NOTIFICATIONS.append(
        {
            "event": "TICKET_STATUS_CHANGED",
            "ticket_id": ticket_id,
            "to": row["executive_name"],
            "message": f"Status moved {old} → {payload.status}",
            "at": datetime.utcnow(),
        }
    )
    return {**row, "transition": transition}


@router.post("/assign/{ticket_id}")
def assign_ticket(ticket_id: int, assigned_to: str):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    row["executive_name"] = assigned_to
    _log("TICKET_ASSIGNED", {"ticket_id": ticket_id, "assigned_to": assigned_to})
    return row


@router.post("/escalate/{ticket_id}")
def escalate_ticket(ticket_id: int, reason: str):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    row["status"] = "ESCALATED"
    row["escalation_reason"] = reason
    _log("TICKET_ESCALATED", {"ticket_id": ticket_id, "reason": reason})
    return row


@router.post("/resolve/{ticket_id}")
def resolve_ticket(ticket_id: int, resolution_note: str):
    if not resolution_note.strip():
        raise HTTPException(status_code=422, detail="Resolution note mandatory before close if policy enabled")
    return update_ticket_status(ticket_id, TicketStatusUpdateRequest(status="RESOLVED", actor="SYSTEM", actor_role="Admin", remark=resolution_note, approval_granted=True))


@router.post("/close/{ticket_id}")
def close_ticket(ticket_id: int, resolution_note: str):
    if not resolution_note.strip():
        raise HTTPException(status_code=422, detail="Resolution note mandatory before close if policy enabled")
    FOLLOWUPS.setdefault(ticket_id, []).append({"followup_id": len(FOLLOWUPS.get(ticket_id, [])) + 1, "remark": resolution_note, "status": "RESOLVED", "at": datetime.utcnow()})
    return update_ticket_status(ticket_id, TicketStatusUpdateRequest(status="CLOSED", actor="SYSTEM", actor_role="Admin", remark=resolution_note, approval_granted=True))


@router.get("/{ticket_id}/followups")
def list_followups(ticket_id: int):
    get_ticket(ticket_id)
    return FOLLOWUPS.get(ticket_id, [])


@router.post("/{ticket_id}/followups")
def create_followup(ticket_id: int, payload: FollowupCreateRequest):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")

    validate_status_transition(
        module=ModuleType.ticket,
        from_status=row["status"],
        to_status=payload.status,
        actor_role="Assigned User",
        approval_granted=True,
    )

    followups = FOLLOWUPS[ticket_id]
    next_id = len(followups) + 1
    record = {
        "followup_id": next_id,
        **payload.model_dump(),
        "at": datetime.utcnow(),
        "time_spent_minutes": 0,
    }
    followups.append(record)

    old = row["status"]
    row["status"] = payload.status
    row["updated_at"] = datetime.utcnow()
    row["total_effort_minutes"] += record["time_spent_minutes"]

    _log("FOLLOWUP_CREATED", {"ticket_id": ticket_id, "followup_id": next_id, "from": old, "to": payload.status})
    NOTIFICATIONS.append(
        {
            "event": "FOLLOWUP_CREATED",
            "ticket_id": ticket_id,
            "to": row["executive_name"],
            "message": "Followup logged",
            "at": datetime.utcnow(),
        }
    )
    return record


@router.post("/comment/{ticket_id}")
def add_ticket_comment(ticket_id: int, comment: str):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    FOLLOWUPS.setdefault(ticket_id, []).append({"followup_id": len(FOLLOWUPS.get(ticket_id, [])) + 1, "followup_type": "COMMENT", "remark": comment, "status": row["status"], "executive_name": row["executive_name"], "at": datetime.utcnow(), "time_spent_minutes": 0})
    _log("TICKET_COMMENT_ADDED", {"ticket_id": ticket_id})
    return {"status": "comment_added", "ticket_id": ticket_id}


@router.post("/reopen/{ticket_id}")
def reopen_ticket(ticket_id: int, reason: str):
    row = TICKETS.get(ticket_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    row["status"] = "REOPENED"
    row["reopen_reason"] = reason
    _log("TICKET_REOPENED", {"ticket_id": ticket_id, "reason": reason})
    return row


@router.get("/dashboard/summary")
def ticket_dashboard():
    rows = list(TICKETS.values())
    total = len(rows)
    closed = len([r for r in rows if r["status"] == "CLOSED"])
    open_count = total - closed
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    sla_breached = len([r for r in rows if _sla_indicator(r) == "BREACHED"])
    total_collected = sum(
        (f.get("amount_collected") or 0.0)
        for followups in FOLLOWUPS.values()
        for f in followups
    )
    total_expenses = sum(
        (f.get("travelling_expenses") or 0.0)
        for followups in FOLLOWUPS.values()
        for f in followups
    )

    return {
        "execution": {
            "tickets_total": total,
            "tickets_open": open_count,
            "tickets_closed": closed,
            "followups_total": sum(len(v) for v in FOLLOWUPS.values()),
        },
        "financial": {
            "amount_collected": total_collected,
            "travelling_expenses": total_expenses,
            "net": total_collected - total_expenses,
        },
        "sla": {
            "breached": sla_breached,
            "on_track": len([r for r in rows if _sla_indicator(r) == "ON_TRACK"]),
            "warning": len([r for r in rows if _sla_indicator(r) == "WARNING"]),
        },
        "status_distribution": by_status,
    }


@router.get("/reports/summary")
def ticket_reports():
    rows = list(TICKETS.values())
    by_priority: dict[str, int] = {}
    for row in rows:
        key = row["priority"]
        by_priority[key] = by_priority.get(key, 0) + 1

    return {
        "ticket_summary": {
            "total": len(rows),
            "closed": len([r for r in rows if r["status"] == "CLOSED"]),
        },
        "tickets_by_status": ticket_dashboard()["status_distribution"],
        "ticket_sla_report": ticket_dashboard()["sla"],
        "executive_performance": [
            {"executive": k, "tickets": len([r for r in rows if r["executive_name"] == k])}
            for k in sorted({r["executive_name"] for r in rows})
        ],
        "followup_report": {"total_followups": sum(len(v) for v in FOLLOWUPS.values())},
        "tickets_by_priority": by_priority,
    }


@router.get("/analytics/summary")
def ticket_analytics():
    rows = list(TICKETS.values())
    repeat_issues: dict[str, int] = {}
    for r in rows:
        key = f"{r['customer_name']}::{r['category']}"
        repeat_issues[key] = repeat_issues.get(key, 0) + 1

    return {
        "tickets_by_priority": ticket_reports()["tickets_by_priority"],
        "resolution_time_hours": 0,
        "sla_compliance_pct": 0 if not rows else round((len([r for r in rows if _sla_indicator(r) != "BREACHED"]) * 100) / len(rows), 2),
        "repeat_issues": sorted(repeat_issues.items(), key=lambda x: x[1], reverse=True)[:10],
    }


@router.get("/notifications")
def ticket_notifications():
    return NOTIFICATIONS


@router.get("/audit-log")
def ticket_audit_log():
    return TICKET_AUDIT


@router.post("/sync")
def sync_ticket(payload: TicketCreateRequest):
    # Baseline ERP sync hook delegates to ticket creation.
    ticket = create_ticket(payload)
    _log("TICKET_SYNCED", {"ticket_id": ticket["ticket_id"]})
    return {"sync": "ok", "ticket": ticket}
