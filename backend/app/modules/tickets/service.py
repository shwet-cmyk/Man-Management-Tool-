from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_ticket import WmTicket
from app.models.wm_ticket_comment import WmTicketComment
from app.models.wm_ticket_history import WmTicketHistory
from app.models.wm_ticket_user import WmTicketUser
from app.modules.sla.schemas import SlaStartRequest
from app.modules.sla.service import SlaService
from app.modules.tickets.schemas import TicketAssignRequest, TicketCommentRequest, TicketCreateRequest, TicketUpdateRequest
from app.modules.workflows.schemas import TriggerWorkflowRequest
from app.modules.workflows.service import WorkflowService


class TicketService:
    def __init__(self, db: Session):
        self.db = db

    def create_ticket(self, payload: TicketCreateRequest):
        dup = (
            self.db.query(WmTicket)
            .filter(
                WmTicket.subject == payload.subject,
                WmTicket.customer_id == payload.customer_id,
                WmTicket.status.in_(["NEW", "ASSIGNED", "IN_PROGRESS", "WAITING"]),
                WmTicket.created_on >= datetime.utcnow() - timedelta(days=1),
            )
            .first()
        )
        if dup:
            return {"ticket_id": dup.ticket_id, "ticket_no": dup.ticket_no, "message": "Duplicate open ticket exists"}

        ticket = WmTicket(
            ticket_no=f"TKT-{int(datetime.utcnow().timestamp())}",
            customer_id=payload.customer_id,
            subject=payload.subject,
            description=payload.description,
            priority=payload.priority.upper(),
            status="NEW",
            channel=payload.channel.upper(),
            created_by=payload.created_by,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            department_id=payload.department_id,
        )
        self.db.add(ticket)
        self.db.flush()

        users = payload.assigned_users[:]
        if payload.auto_assign and not users:
            users = self._auto_assign(payload.department_id)
        for uid in users:
            self.db.add(WmTicketUser(ticket_id=ticket.ticket_id, user_id=uid, role="OWNER"))
        if users:
            ticket.status = "ASSIGNED"

        self.db.add(WmTicketHistory(ticket_id=ticket.ticket_id, field="status", old_value=None, new_value=ticket.status, changed_by=payload.created_by))

        # SLA start (if rule exists)
        try:
            SlaService(self.db).start_sla(
                SlaStartRequest(
                    module="TICKET",
                    entity_type="TICKET",
                    entity_id=ticket.ticket_id,
                    assignee_user_id=users[0] if users else None,
                    company_id=payload.company_id,
                    branch_id=payload.branch_id,
                    context={"priority": ticket.priority, "channel": ticket.channel},
                )
            )
        except Exception:
            pass

        # workflow trigger (best effort)
        try:
            WorkflowService(self.db).trigger_workflow(
                TriggerWorkflowRequest(
                    module="TICKET",
                    event_name="TICKET_CREATED",
                    entity_type="TICKET",
                    entity_id=ticket.ticket_id,
                    context={"priority": ticket.priority, "channel": ticket.channel},
                )
            )
        except Exception:
            pass

        self.db.commit()
        self.db.refresh(ticket)
        return {"ticket_id": ticket.ticket_id, "ticket_no": ticket.ticket_no, "status": ticket.status}

    def update_ticket(self, ticket_id: int, payload: TicketUpdateRequest):
        t = self._get(ticket_id)
        changes = []

        def set_field(name, value):
            old = getattr(t, name)
            if value is not None and value != old:
                setattr(t, name, value)
                changes.append((name, old, value))

        set_field("status", payload.status)
        set_field("priority", payload.priority.upper() if payload.priority else None)
        set_field("subject", payload.subject)
        set_field("description", payload.description)
        set_field("resolution_note", payload.resolution_note)

        if payload.status == "CLOSED" and not (payload.resolution_note or t.resolution_note):
            raise HTTPException(status_code=422, detail="Ticket cannot close without resolution note")

        t.updated_on = datetime.utcnow()
        for field, old, new in changes:
            self.db.add(WmTicketHistory(ticket_id=t.ticket_id, field=field, old_value=str(old) if old is not None else None, new_value=str(new) if new is not None else None, changed_by=payload.changed_by))

        self.db.commit()
        return {"ticket_id": t.ticket_id, "status": t.status}

    def add_comment(self, ticket_id: int, payload: TicketCommentRequest):
        t = self._get(ticket_id)
        c = WmTicketComment(ticket_id=ticket_id, user_id=payload.user_id, message=payload.message, is_internal=payload.is_internal, attachments=json.dumps(payload.attachments))
        self.db.add(c)

        # customer reply should move waiting to in progress
        if not payload.is_internal and t.status == "WAITING":
            old = t.status
            t.status = "IN_PROGRESS"
            self.db.add(WmTicketHistory(ticket_id=t.ticket_id, field="status", old_value=old, new_value=t.status, changed_by=payload.user_id))

        self.db.commit()
        return {"comment_id": c.comment_id}

    def assign_users(self, ticket_id: int, payload: TicketAssignRequest):
        t = self._get(ticket_id)
        for uid in payload.user_ids:
            exists = self.db.query(WmTicketUser).filter(WmTicketUser.ticket_id == ticket_id, WmTicketUser.user_id == uid, WmTicketUser.role == payload.role).first()
            if not exists:
                self.db.add(WmTicketUser(ticket_id=ticket_id, user_id=uid, role=payload.role))
        old = t.status
        if t.status == "NEW":
            t.status = "ASSIGNED"
        self.db.add(WmTicketHistory(ticket_id=t.ticket_id, field="status", old_value=old, new_value=t.status, changed_by=payload.user_ids[0] if payload.user_ids else 0))
        self.db.commit()
        return {"ticket_id": t.ticket_id, "status": t.status}

    def timeline(self, ticket_id: int):
        t = self._get(ticket_id)
        comments = self.db.query(WmTicketComment).filter(WmTicketComment.ticket_id == ticket_id).order_by(WmTicketComment.created_at.asc()).all()
        history = self.db.query(WmTicketHistory).filter(WmTicketHistory.ticket_id == ticket_id).order_by(WmTicketHistory.changed_at.asc()).all()
        users = self.db.query(WmTicketUser).filter(WmTicketUser.ticket_id == ticket_id).all()
        return {
            "ticket": {"ticket_id": t.ticket_id, "ticket_no": t.ticket_no, "status": t.status, "subject": t.subject, "priority": t.priority},
            "users": [{"user_id": u.user_id, "role": u.role, "assigned_at": u.assigned_at} for u in users],
            "comments": [{"comment_id": c.comment_id, "user_id": c.user_id, "message": c.message, "is_internal": c.is_internal, "attachments": c.attachments, "created_at": c.created_at} for c in comments],
            "history": [{"field": h.field, "old_value": h.old_value, "new_value": h.new_value, "changed_by": h.changed_by, "changed_at": h.changed_at} for h in history],
        }

    def _auto_assign(self, department_id: int | None):
        # simple deterministic fallback
        return [department_id + 1000] if department_id else [1001]

    def _get(self, ticket_id: int):
        t = self.db.query(WmTicket).filter(WmTicket.ticket_id == ticket_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return t
