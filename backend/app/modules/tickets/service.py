from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.wm_task import WmTask
from app.models.wm_ticket import WmTicket
from app.models.wm_ticket_comment import WmTicketComment
from app.models.wm_ticket_escalation_log import WmTicketEscalationLog
from app.models.wm_ticket_followup import WmTicketFollowup
from app.models.wm_ticket_history import WmTicketHistory
from app.models.wm_ticket_pause_history import WmTicketPauseHistory
from app.models.wm_ticket_task_link import WmTicketTaskLink
from app.models.wm_ticket_user import WmTicketUser
from app.modules.tickets.business_calendar_service import BusinessCalendarService
from app.modules.tickets.dashboard_aggregation_service import DashboardAggregationService
from app.modules.tickets.escalation_service import EscalationService
from app.modules.tickets.rollover_service import RolloverService
from app.modules.tickets.schemas import (
    EscalationDigestRequest,
    TaskRolloverRequest,
    TicketAssignRequest,
    TicketCommentRequest,
    TicketConvertToTaskRequest,
    TicketCreateRequest,
    TicketDashboardRequest,
    TicketFollowupRequest,
    TicketPauseRequest,
    TicketUpdateRequest,
)
from app.modules.tickets.sla_engine import SlaEngine
from app.modules.tickets.validation_service import ValidationService


class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.calendar = BusinessCalendarService()
        self.sla_engine = SlaEngine(self.calendar)
        self.validation = ValidationService()
        self.escalation = EscalationService(db)
        self.rollover = RolloverService(db)

    def create_ticket(self, payload: TicketCreateRequest):
        self.validation.validate_priority(payload.priority)

        now = datetime.utcnow()
        status = "ASSIGNED" if payload.assign_executive_id else "OPEN"
        response_due, closure_due = self.sla_engine.due_times(now, payload.priority)

        ticket = WmTicket(
            ticket_no=f"TKT-{int(now.timestamp())}",
            external_ticket_no=payload.external_ticket_no,
            customer_id=payload.customer_id,
            customer_name=payload.customer_name,
            product=payload.product,
            license_name_or_package=payload.license_name_or_package,
            remark=payload.remark,
            category=payload.category,
            ticket_type=payload.type,
            subject=payload.subject,
            description=payload.description,
            priority=payload.priority.upper(),
            status=status,
            channel=payload.channel.upper(),
            assign_executive_id=payload.assign_executive_id,
            assign_executive_name=payload.assign_executive_name,
            created_by=payload.created_by,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            department_id=payload.department_id,
            mobile=payload.mobile,
            contact_person=payload.contact_person,
            email=payload.email,
            address=payload.address,
            pack_validity=datetime.fromisoformat(payload.pack_validity) if payload.pack_validity else None,
            sms_balance=payload.sms_balance,
            whatsapp_balance=payload.whatsapp_balance,
            username=payload.username,
            max_user=payload.max_user,
            attachments=json.dumps(payload.attachments),
            assigned_on=now if payload.assign_executive_id else None,
            response_sla_due_at=response_due,
            closure_sla_due_at=closure_due,
            response_sla_status="PENDING",
            closure_sla_status="PENDING",
            is_critical=payload.priority.upper() == "HIGH",
            created_on=now,
            created_at=now,
            updated_at=now,
            updated_by=payload.created_by,
        )
        self.db.add(ticket)
        self.db.flush()

        if payload.assign_executive_id:
            self.db.add(WmTicketUser(ticket_id=ticket.ticket_id, user_id=payload.assign_executive_id, role="OWNER"))

        self._audit(ticket.ticket_id, "ticket_created", payload.created_by, None, status)
        self.db.commit()
        return {
            "ticket_id": ticket.ticket_id,
            "ticket_no": ticket.ticket_no,
            "response_sla_due_at": ticket.response_sla_due_at,
            "closure_sla_due_at": ticket.closure_sla_due_at,
            "status": ticket.status,
        }

    def update_ticket(self, ticket_id: int, payload: TicketUpdateRequest):
        ticket = self._get(ticket_id)
        now = datetime.utcnow()
        if payload.priority:
            self.validation.validate_priority(payload.priority)

        if payload.status:
            self.validation.validate_transition(ticket.status, payload.status)
            self.validation.validate_waiting_transition(payload.status, payload.pause_reason)
            self.validation.validate_closure(payload.status, payload.resolution_note or ticket.resolution_note)

            prev = ticket.status
            ticket.status = payload.status.upper()
            if ticket.status == "RESOLVED":
                ticket.resolved_at = now
            if ticket.status == "CLOSED":
                ticket.closed_at = now
            if ticket.status == "REOPENED":
                ticket.reopened_at = now
                ticket.reopen_count += 1
            self._audit(ticket.ticket_id, "status_changed", payload.changed_by, prev, ticket.status)

            if payload.status.upper() in {"WAITING_FOR_CUSTOMER", "WAITING_FOR_INTERNAL_TEAM"}:
                self._pause_ticket(ticket, payload.pause_reason or "Waiting state", payload.changed_by)
            elif ticket.response_sla_paused or ticket.closure_sla_paused:
                self._resume_ticket(ticket, payload.changed_by)

        if payload.priority and payload.priority.upper() != ticket.priority:
            self._audit(ticket.ticket_id, "priority_changed", payload.changed_by, ticket.priority, payload.priority.upper())
            ticket.priority = payload.priority.upper()

        if payload.subject:
            ticket.subject = payload.subject
        if payload.description:
            ticket.description = payload.description
        if payload.resolution_note:
            ticket.resolution_note = payload.resolution_note
        if payload.remark:
            ticket.remark = payload.remark

        ticket.updated_on = now
        ticket.updated_at = now
        ticket.updated_by = payload.changed_by

        self._refresh_sla(ticket, now)
        self._refresh_escalation(ticket, now)
        self.db.commit()
        return {"ticket_id": ticket.ticket_id, "status": ticket.status, "escalation_level": ticket.escalation_level}

    def add_comment(self, ticket_id: int, payload: TicketCommentRequest):
        ticket = self._get(ticket_id)
        comment = WmTicketComment(
            ticket_id=ticket_id,
            user_id=payload.user_id,
            message=payload.message,
            is_internal=payload.is_internal,
            attachments=json.dumps(payload.attachments),
        )
        self.db.add(comment)

        note = payload.message.strip()
        if not payload.is_internal and note:
            self._capture_first_response(ticket, note, payload.user_id)

        ticket.last_followup_at = datetime.utcnow()
        ticket.last_followup_by = payload.user_id
        self._audit(ticket.ticket_id, "comment_added", payload.user_id, None, note)

        self.db.commit()
        return {"comment_id": comment.comment_id}

    def assign_users(self, ticket_id: int, payload: TicketAssignRequest):
        ticket = self._get(ticket_id)
        for uid in payload.user_ids:
            exists = (
                self.db.query(WmTicketUser)
                .filter(WmTicketUser.ticket_id == ticket_id, WmTicketUser.user_id == uid, WmTicketUser.role == payload.role)
                .first()
            )
            if not exists:
                self.db.add(WmTicketUser(ticket_id=ticket_id, user_id=uid, role=payload.role))

        old = ticket.status
        if ticket.status in {"OPEN", "REOPENED"}:
            ticket.status = "ASSIGNED"
        ticket.assigned_on = datetime.utcnow()
        ticket.assign_executive_id = payload.user_ids[0] if payload.user_ids else ticket.assign_executive_id
        self._audit(ticket.ticket_id, "assignment_changed", payload.user_ids[0] if payload.user_ids else 0, old, ticket.status)

        self.db.commit()
        return {"ticket_id": ticket.ticket_id, "status": ticket.status}

    def add_followup(self, ticket_id: int, payload: TicketFollowupRequest):
        ticket = self._get(ticket_id)
        if payload.new_status:
            self.validation.validate_transition(ticket.status, payload.new_status)
        self.validation.validate_first_response_note(payload.note)

        row = WmTicketFollowup(
            ticket_id=ticket_id,
            action_type=payload.action_type,
            previous_status=payload.previous_status or ticket.status,
            new_status=payload.new_status,
            note=payload.note,
            created_by=payload.created_by,
            is_customer_visible=payload.is_customer_visible,
            attachment_refs=json.dumps(payload.attachment_refs),
        )
        self.db.add(row)

        if payload.new_status:
            old = ticket.status
            ticket.status = payload.new_status.upper()
            self._audit(ticket.ticket_id, "status_changed", payload.created_by, old, ticket.status)

        self._capture_first_response(ticket, payload.note, payload.created_by)
        ticket.last_followup_at = datetime.utcnow()
        ticket.last_followup_by = payload.created_by
        self.db.commit()
        return {"followup_id": row.followup_id}

    def pause_or_resume(self, ticket_id: int, payload: TicketPauseRequest):
        ticket = self._get(ticket_id)
        if payload.paused:
            self._pause_ticket(ticket, payload.reason, payload.changed_by)
        else:
            self._resume_ticket(ticket, payload.changed_by)
        self.db.commit()
        return {"ticket_id": ticket.ticket_id, "paused": ticket.response_sla_paused or ticket.closure_sla_paused, "total_pause_minutes": ticket.total_pause_minutes}

    def convert_to_task(self, ticket_id: int, payload: TicketConvertToTaskRequest):
        ticket = self._get(ticket_id)
        task = WmTask(
            task_no=f"TSK-TKT-{ticket.ticket_id}-{int(datetime.utcnow().timestamp())}",
            title=ticket.subject,
            description=ticket.remark or ticket.description,
            priority_code=(payload.override_priority or ticket.priority).upper().title(),
            customer_id=ticket.customer_id,
            source_type="TICKET",
            source_reference=ticket.ticket_no,
            company_id=ticket.company_id,
            branch_id=ticket.branch_id,
            department_id=ticket.department_id,
            created_by=payload.created_by,
            status_code="Open",
            lifecycle_state="ACTIVE",
        )
        self.db.add(task)
        self.db.flush()
        self.db.add(WmTicketTaskLink(ticket_id=ticket.ticket_id, task_id=task.task_id, source="TICKET"))
        self._audit(ticket.ticket_id, "ticket_converted_to_task", payload.created_by, None, str(task.task_id))
        self.db.commit()
        return {"ticket_id": ticket.ticket_id, "task_id": task.task_id}

    def register_task_rollover(self, payload: TaskRolloverRequest):
        previous_due_at = datetime.fromisoformat(payload.previous_due_at)
        revised_due_at = datetime.fromisoformat(payload.revised_due_at)
        self.validation.validate_rollover(previous_due_at, revised_due_at, payload.reason)

        out = self.rollover.register_rollover(
            task_id=payload.task_id,
            previous_due_at=previous_due_at,
            revised_due_at=revised_due_at,
            changed_by=payload.changed_by,
            reason=payload.reason,
            remarks=payload.remarks,
        )
        self._audit(0, "task_rollover", payload.changed_by, payload.previous_due_at, payload.revised_due_at)
        self.db.commit()
        return out

    def dashboard_metrics(self, payload: TicketDashboardRequest):
        return {
            "ticket_dashboard": DashboardAggregationService(self.db).ticket_metrics(stale_window_minutes=payload.stale_window_minutes),
            "rollover_dashboard": DashboardAggregationService(self.db).rollover_metrics(),
        }

    def daily_escalation_digest(self, payload: EscalationDigestRequest):
        digest = DashboardAggregationService(self.db).escalation_digest_payload()
        digest["scheduled_for"] = payload.run_at or "21:30"
        return digest

    def timeline(self, ticket_id: int):
        ticket = self._get(ticket_id)
        comments = self.db.query(WmTicketComment).filter(WmTicketComment.ticket_id == ticket_id).order_by(WmTicketComment.created_at.asc()).all()
        history = self.db.query(WmTicketHistory).filter(WmTicketHistory.ticket_id == ticket_id).order_by(WmTicketHistory.changed_at.asc()).all()
        followups = self.db.query(WmTicketFollowup).filter(WmTicketFollowup.ticket_id == ticket_id).order_by(WmTicketFollowup.created_at.asc()).all()
        pauses = self.db.query(WmTicketPauseHistory).filter(WmTicketPauseHistory.ticket_id == ticket_id).order_by(WmTicketPauseHistory.pause_start.asc()).all()
        escalations = self.db.query(WmTicketEscalationLog).filter(WmTicketEscalationLog.ticket_id == ticket_id).order_by(WmTicketEscalationLog.created_at.asc()).all()
        users = self.db.query(WmTicketUser).filter(WmTicketUser.ticket_id == ticket_id).all()
        return {
            "ticket": {
                "ticket_id": ticket.ticket_id,
                "ticket_no": ticket.ticket_no,
                "status": ticket.status,
                "priority": ticket.priority,
                "response_sla_status": ticket.response_sla_status,
                "closure_sla_status": ticket.closure_sla_status,
                "escalation_level": ticket.escalation_level,
                "aging_minutes": ticket.aging_minutes,
            },
            "users": [{"user_id": u.user_id, "role": u.role, "assigned_at": u.assigned_at} for u in users],
            "comments": [{"comment_id": c.comment_id, "user_id": c.user_id, "message": c.message, "is_internal": c.is_internal, "created_at": c.created_at} for c in comments],
            "followups": [{"followup_id": f.followup_id, "action_type": f.action_type, "previous_status": f.previous_status, "new_status": f.new_status, "note": f.note, "created_by": f.created_by, "created_at": f.created_at} for f in followups],
            "pauses": [{"pause_id": p.pause_id, "pause_start": p.pause_start, "pause_end": p.pause_end, "pause_reason": p.pause_reason, "total_minutes": p.total_minutes} for p in pauses],
            "escalations": [{"level": e.escalation_level, "trigger": e.trigger_key, "recipients": e.recipients, "created_at": e.created_at} for e in escalations],
            "history": [{"field": h.field, "old_value": h.old_value, "new_value": h.new_value, "changed_by": h.changed_by, "changed_at": h.changed_at} for h in history],
        }

    def _capture_first_response(self, ticket: WmTicket, note: str, user_id: int):
        qualifies = bool(note and len(note.strip()) >= 3 and ticket.status.upper() not in {"OPEN", "ASSIGNED"})
        if not ticket.first_response_at and qualifies:
            ticket.first_response_at = datetime.utcnow()
            ticket.response_sla_status, ticket.response_delay_minutes = self.sla_engine.compute_status(ticket.first_response_at, ticket.response_sla_due_at, datetime.utcnow())
            self._audit(ticket.ticket_id, "first_response_captured", user_id, None, ticket.first_response_at.isoformat())

    def _refresh_sla(self, ticket: WmTicket, now: datetime):
        ticket.response_sla_status, ticket.response_delay_minutes = self.sla_engine.compute_status(ticket.first_response_at, ticket.response_sla_due_at, now)
        ticket.closure_sla_status, ticket.closure_delay_minutes = self.sla_engine.compute_status(ticket.closed_at, ticket.closure_sla_due_at, now)
        ticket.aging_minutes = self.calendar.calculate_elapsed_working_minutes(ticket.created_on, now)

    def _refresh_escalation(self, ticket: WmTicket, now: datetime):
        level, trigger = self.escalation.evaluate_level(ticket, now)
        if level > ticket.escalation_level:
            recipients = [f"EXEC-{ticket.assign_executive_id or 0}", f"MGR-{ticket.department_id or 0}"]
            self.escalation.log_escalation(ticket.ticket_id, level, trigger, recipients)
            ticket.escalation_level = level
            ticket.escalation_status = trigger
            self._audit(ticket.ticket_id, "escalation_triggered", ticket.updated_by or ticket.created_by, str(level), trigger)

    def _pause_ticket(self, ticket: WmTicket, reason: str, changed_by: int):
        now = datetime.utcnow()
        ticket.response_sla_paused = True
        ticket.closure_sla_paused = True
        self.db.add(WmTicketPauseHistory(ticket_id=ticket.ticket_id, pause_start=now, pause_reason=reason, paused_by=changed_by))
        self._audit(ticket.ticket_id, "sla_paused", changed_by, None, reason)

    def _resume_ticket(self, ticket: WmTicket, changed_by: int):
        now = datetime.utcnow()
        row = (
            self.db.query(WmTicketPauseHistory)
            .filter(WmTicketPauseHistory.ticket_id == ticket.ticket_id, WmTicketPauseHistory.pause_end.is_(None))
            .order_by(WmTicketPauseHistory.pause_start.desc())
            .first()
        )
        if row:
            row.pause_end = now
            row.total_minutes = self.calendar.calculate_elapsed_working_minutes(row.pause_start, now)
            ticket.total_pause_minutes += int(row.total_minutes or 0)
            if ticket.response_sla_due_at:
                ticket.response_sla_due_at = self.calendar.add_working_minutes(ticket.response_sla_due_at, int(row.total_minutes or 0))
            if ticket.closure_sla_due_at:
                ticket.closure_sla_due_at = self.calendar.add_working_minutes(ticket.closure_sla_due_at, int(row.total_minutes or 0))
        ticket.response_sla_paused = False
        ticket.closure_sla_paused = False
        self._audit(ticket.ticket_id, "sla_resumed", changed_by, None, str(ticket.total_pause_minutes))

    def _audit(self, ticket_id: int, field: str, changed_by: int, old_value, new_value):
        self.db.add(
            WmTicketHistory(
                ticket_id=ticket_id,
                field=field,
                old_value=None if old_value is None else str(old_value),
                new_value=None if new_value is None else str(new_value),
                changed_by=changed_by,
            )
        )

    def _get(self, ticket_id: int):
        ticket = self.db.query(WmTicket).filter(WmTicket.ticket_id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket
