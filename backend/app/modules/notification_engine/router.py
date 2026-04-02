from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry

router = APIRouter(prefix="/notifications", tags=["Unified Notification Engine"])


class ChannelType(str, Enum):
    in_app = "IN_APP"
    email = "EMAIL"
    push = "PUSH"
    chat = "CHAT"


class DeliveryStatus(str, Enum):
    sent = "SENT"
    delivered = "DELIVERED"
    failed = "FAILED"


class ReadStatus(str, Enum):
    unread = "UNREAD"
    read = "READ"
    clicked = "CLICKED"


class TriggerEvent(str, Enum):
    sla_reminder = "SLA_REMINDER"
    project_event = "PROJECT_EVENT"
    ticket_event = "TICKET_EVENT"
    approval_event = "APPROVAL_EVENT"
    escalation_event = "ESCALATION_EVENT"


class TriggerRequest(BaseModel):
    module: str
    event_type: TriggerEvent
    recipient_user: str
    channel: ChannelType = ChannelType.in_app
    template_name: str
    variables: dict = Field(default_factory=dict)
    linked_ref: str


NOTIFICATION_TEMPLATES = {
    "TASK_DUE_REMINDER": "Dear #Employee Name#, Task #Task Name# is due on #Due Date#.",
    "PROJECT_DELAY_ALERT": "Project #Project Name# is delayed. Current status: #Status#.",
    "TICKET_UPDATE": "Ticket #Ticket Number# moved to #Status#.",
    "APPROVAL_REQUIRED": "Approval required for #Module# #Reference#.",
    "ESCALATION_NOTICE": "Escalation triggered for #Module# #Reference# due to no action.",
}

NOTIFICATION_LOGS: dict[int, dict] = {}


def _render(template: str, variables: dict) -> str:
    result = template
    for key, value in variables.items():
        result = result.replace(f"#{key}#", str(value))
    return result


def _create_log(payload: TriggerRequest, message: str, delivery_status: DeliveryStatus = DeliveryStatus.sent):
    next_id = len(NOTIFICATION_LOGS) + 1
    row = {
        "notification_id": next_id,
        "date_time": datetime.utcnow(),
        "module": payload.module,
        "event_type": payload.event_type,
        "template_name": payload.template_name,
        "recipient_user": payload.recipient_user,
        "channel_type": payload.channel,
        "delivery_status": delivery_status,
        "read_status": ReadStatus.unread,
        "template_variables": payload.variables,
        "final_message": message,
        "linked_ref": payload.linked_ref,
        "sent_at": datetime.utcnow(),
        "delivered_at": datetime.utcnow() if delivery_status != DeliveryStatus.failed else None,
        "read_at": None,
        "clicked_at": None,
        "trigger_event": payload.event_type,
        "escalated": False,
    }
    NOTIFICATION_LOGS[next_id] = row

    add_audit_entry(
        AuditCreateRequest(
            user_name="SYSTEM",
            module="NOTIFICATION",
            reference_id=str(next_id),
            action_type="NOTIFICATION_SENT" if delivery_status != DeliveryStatus.failed else "NOTIFICATION_FAILED",
            field_name="delivery_status",
            old_value=None,
            new_value=str(delivery_status),
            remarks=payload.template_name,
            context={
                "module": payload.module,
                "recipient": payload.recipient_user,
                "channel": payload.channel,
                "linked_ref": payload.linked_ref,
            },
        )
    )

    return row


@router.post("/trigger")
def trigger_notification(payload: TriggerRequest):
    template = NOTIFICATION_TEMPLATES.get(payload.template_name)
    if not template:
        raise HTTPException(status_code=422, detail="Unknown template")

    message = _render(template, payload.variables)
    return _create_log(payload=payload, message=message)


@router.get("/{user}")
def list_notifications(user: str, unread_only: bool = False):
    rows = [r for r in NOTIFICATION_LOGS.values() if r["recipient_user"] == user]
    if unread_only:
        rows = [r for r in rows if r["read_status"] == ReadStatus.unread]
    return sorted(rows, key=lambda x: x["date_time"], reverse=True)


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, clicked: bool = False):
    row = NOTIFICATION_LOGS.get(notification_id)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")

    old = row["read_status"]
    row["read_status"] = ReadStatus.clicked if clicked else ReadStatus.read
    row["read_at"] = datetime.utcnow()
    if clicked:
        row["clicked_at"] = datetime.utcnow()

    add_audit_entry(
        AuditCreateRequest(
            user_name=row["recipient_user"],
            module="NOTIFICATION",
            reference_id=str(notification_id),
            action_type="NOTIFICATION_READ" if not clicked else "NOTIFICATION_CLICKED",
            field_name="read_status",
            old_value=str(old),
            new_value=str(row["read_status"]),
            remarks=None,
        )
    )
    return row


@router.post("/escalations/run")
def run_notification_escalations(hours_unread: int = 24):
    now = datetime.utcnow()
    escalated = []
    for row in NOTIFICATION_LOGS.values():
        if row["read_status"] != ReadStatus.unread:
            continue
        if row["escalated"]:
            continue
        if row["sent_at"] + timedelta(hours=hours_unread) > now:
            continue

        row["escalated"] = True
        escalated.append(row["notification_id"])
        add_audit_entry(
            AuditCreateRequest(
                user_name="SYSTEM",
                module="NOTIFICATION",
                reference_id=str(row["notification_id"]),
                action_type="ESCALATION_TRIGGERED",
                field_name="escalated",
                old_value=False,
                new_value=True,
                remarks="Unread threshold exceeded",
            )
        )

    return {"count": len(escalated), "notification_ids": escalated}


@router.get("/audit/logs")
def notification_audit_logs(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    module: str | None = None,
    user: str | None = None,
    channel_type: ChannelType | None = None,
    delivery_status: DeliveryStatus | None = None,
    read_status: ReadStatus | None = None,
):
    rows = list(NOTIFICATION_LOGS.values())
    if date_from:
        rows = [r for r in rows if r["date_time"] >= date_from]
    if date_to:
        rows = [r for r in rows if r["date_time"] <= date_to]
    if module:
        rows = [r for r in rows if r["module"] == module]
    if user:
        rows = [r for r in rows if r["recipient_user"] == user]
    if channel_type:
        rows = [r for r in rows if r["channel_type"] == channel_type]
    if delivery_status:
        rows = [r for r in rows if r["delivery_status"] == delivery_status]
    if read_status:
        rows = [r for r in rows if r["read_status"] == read_status]
    return rows


@router.get("/audit/{notification_id}")
def notification_audit_detail(notification_id: int):
    row = NOTIFICATION_LOGS.get(notification_id)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {
        "message_info": {
            "template_used": row["template_name"],
            "final_message": row["final_message"],
            "variables": row["template_variables"],
        },
        "delivery_trace": {
            "sent_at": row["sent_at"],
            "delivered_at": row["delivered_at"],
            "read_at": row["read_at"],
            "clicked_at": row["clicked_at"],
            "delivery_status": row["delivery_status"],
            "read_status": row["read_status"],
        },
        "context": {
            "module": row["module"],
            "linked_ref": row["linked_ref"],
            "trigger_event": row["trigger_event"],
            "channel": row["channel_type"],
        },
    }


@router.get("/reports/summary")
def notification_reports():
    rows = list(NOTIFICATION_LOGS.values())
    return {
        "notification_delivery_report": rows,
        "failed_notifications": [r for r in rows if r["delivery_status"] == DeliveryStatus.failed],
        "unread_alerts": [r for r in rows if r["read_status"] == ReadStatus.unread],
        "escalation_logs": [r for r in rows if r["escalated"]],
    }
