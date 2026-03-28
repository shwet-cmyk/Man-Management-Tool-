from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.models.wm_ticket import WmTicket
from app.modules.tasks.schemas import TaskCreateRequest


def _pick(source: dict, *keys, default=None):
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return default


class TicketMapperService:
    """Maps source payload keys to canonical ticket/task payloads.

    Assumption: source systems can emit different field names; mapper attempts ordered fallback keys.
    """

    def to_ticket_record(self, payload: dict, created_by: int = 1) -> dict:
        ticket_no = str(_pick(payload, "ticket_no", "ticketNo", "external_ticket_no", "id", default="")).strip()
        if not ticket_no:
            raise ValueError("Ticket number missing in source payload")

        return {
            "ticket_no": ticket_no,
            "external_ticket_no": str(_pick(payload, "external_ticket_no", "ticket_no", "ticketNo", default=ticket_no)),
            "customer_name": _pick(payload, "customer", "customer_name", "client", "party_name"),
            "product": _pick(payload, "product", "module", "service"),
            "license_name_or_package": _pick(payload, "license", "package", "license_name_or_package"),
            "remark": _pick(payload, "remark", "issue", "notes"),
            "category": _pick(payload, "category", "ticket_category"),
            "status": str(_pick(payload, "status", "ticket_status", default="OPEN")).upper(),
            "ticket_type": _pick(payload, "type", "ticket_type"),
            "priority": str(_pick(payload, "priority", default="MEDIUM")).upper(),
            "assign_executive_id": _pick(payload, "assign_executive", "assign_executive_id", "owner_id"),
            "mobile": _pick(payload, "mobile", "phone"),
            "contact_person": _pick(payload, "contact", "contact_person"),
            "email": _pick(payload, "email"),
            "address": _pick(payload, "address"),
            "company_id": _pick(payload, "company", "company_id"),
            "branch_id": _pick(payload, "branch", "branch_id"),
            "department_id": _pick(payload, "department", "department_id"),
            "attachments": self._normalize_attachments(_pick(payload, "attachments", "files", default=[])),
            "subject": (_pick(payload, "subject") or _pick(payload, "remark") or f"Ticket {ticket_no}")[:300],
            "description": _pick(payload, "description", "remark", "issue", default="No description from source"),
            "created_by": created_by,
            "created_on": self._parse_dt(_pick(payload, "created_on", "created_at", "date")) or datetime.utcnow(),
            "updated_on": self._parse_dt(_pick(payload, "updated_on", "updated_at")),
        }

    def to_task_payload(self, ticket: WmTicket, default_owner_id: int, default_manager_id: int | None = None, default_billable: bool = False) -> TaskCreateRequest:
        title = (ticket.remark or ticket.subject or ticket.description or f"Ticket {ticket.ticket_no}")[:120]
        description = f"[Ticket {ticket.ticket_no}] {ticket.description or ticket.remark or ''}".strip()
        return TaskCreateRequest(
            company_id=ticket.company_id,
            branch_id=ticket.branch_id,
            department_id=ticket.department_id,
            customer_id=ticket.customer_id,
            title=title,
            description=description,
            priority_code=(ticket.priority or "MEDIUM").title(),
            primary_owner_emp_id=default_owner_id,
            manager_emp_id=default_manager_id,
            billable_flag=default_billable,
            estimated_hours=Decimal("1"),
            planned_start=datetime.utcnow(),
            due_at=datetime.utcnow() + timedelta(days=1),
            source_type="API",
            source_reference=ticket.ticket_no,
            save_mode="SUBMIT",
        )

    def _normalize_attachments(self, attachments: list | dict | str) -> str:
        if isinstance(attachments, str):
            return attachments
        if isinstance(attachments, dict):
            return str([attachments])
        if isinstance(attachments, list):
            return str(attachments)
        return "[]"

    def _parse_dt(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
