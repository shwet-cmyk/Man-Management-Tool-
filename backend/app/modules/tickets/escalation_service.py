from __future__ import annotations

from datetime import datetime

from app.models.wm_ticket_escalation_log import WmTicketEscalationLog


class EscalationService:
    def __init__(self, db):
        self.db = db

    def evaluate_level(self, ticket, now: datetime):
        priority = ticket.priority.upper()
        if ticket.status.upper() in {"CLOSED"}:
            return 0, "NONE"

        level = 0
        trigger = "NONE"
        if ticket.response_sla_due_at and not ticket.first_response_at:
            consumed = self._consumption_ratio(ticket.created_on, ticket.response_sla_due_at, now)
            if consumed >= 1:
                level, trigger = 3, "RESPONSE_BREACH"
            elif consumed >= 0.75:
                level, trigger = 2, "RESPONSE_NEARING"
            elif consumed >= 0.5:
                level, trigger = 1, "RESPONSE_WARNING"

        if ticket.closure_sla_due_at and not ticket.closed_at:
            consumed = self._consumption_ratio(ticket.created_on, ticket.closure_sla_due_at, now)
            if consumed >= 1:
                level, trigger = max(level, 4), "CLOSURE_BREACH"
            elif priority == "HIGH" and consumed >= 0.9:
                level, trigger = max(level, 3), "HIGH_PRIORITY_CRITICAL"

        return level, trigger

    def log_escalation(self, ticket_id: int, level: int, trigger: str, recipients: list[str]):
        self.db.add(
            WmTicketEscalationLog(
                ticket_id=ticket_id,
                escalation_level=level,
                trigger_key=trigger,
                recipients=",".join(recipients),
            )
        )

    @staticmethod
    def _consumption_ratio(start_at, due_at, now):
        total = (due_at - start_at).total_seconds()
        if total <= 0:
            return 1
        consumed = (min(now, due_at) - start_at).total_seconds()
        return max(0, min(1.5, consumed / total))
