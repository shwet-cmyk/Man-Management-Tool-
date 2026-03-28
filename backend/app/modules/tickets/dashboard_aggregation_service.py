from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import func

from app.models.wm_task_rollover_history import WmTaskRolloverHistory
from app.models.wm_ticket import WmTicket
from app.models.wm_ticket_followup import WmTicketFollowup


class DashboardAggregationService:
    def __init__(self, db):
        self.db = db

    def ticket_metrics(self, stale_window_minutes: int = 24 * 60):
        now = datetime.utcnow()
        stale_cutoff = now - timedelta(minutes=stale_window_minutes)

        open_statuses = ["OPEN", "ASSIGNED", "IN_PROGRESS", "REOPENED", "WAITING_FOR_CUSTOMER", "WAITING_FOR_INTERNAL_TEAM", "ESCALATED"]
        total_open = self.db.query(WmTicket).filter(func.upper(WmTicket.status).in_(open_statuses)).count()
        overdue = self.db.query(WmTicket).filter(WmTicket.closed_at.is_(None), WmTicket.closure_sla_due_at.is_not(None), WmTicket.closure_sla_due_at < now).count()
        high_open = self.db.query(WmTicket).filter(func.upper(WmTicket.status).in_(open_statuses), func.upper(WmTicket.priority) == "HIGH").count()
        response_breach = self.db.query(WmTicket).filter(WmTicket.response_sla_status == "BREACHED").count()
        closure_breach = self.db.query(WmTicket).filter(WmTicket.closure_sla_status == "BREACHED").count()
        reopened = self.db.query(WmTicket).filter(WmTicket.reopen_count > 0).count()
        stale = self.db.query(WmTicket).filter(func.upper(WmTicket.status).in_(open_statuses), (WmTicket.last_followup_at.is_(None)) | (WmTicket.last_followup_at < stale_cutoff)).count()

        exec_wise = (
            self.db.query(WmTicket.assign_executive_id, func.count(WmTicket.ticket_id))
            .filter(func.upper(WmTicket.status).in_(open_statuses))
            .group_by(WmTicket.assign_executive_id)
            .all()
        )

        return {
            "total_open_tickets": total_open,
            "overdue": overdue,
            "high_priority_open": high_open,
            "response_sla_breaches": response_breach,
            "closure_sla_breaches": closure_breach,
            "stale_tickets": stale,
            "reopened_tickets": reopened,
            "executive_wise_open_count": [{"executive_id": eid, "count": c} for eid, c in exec_wise],
        }

    def rollover_metrics(self):
        today = datetime.utcnow().date()
        total = self.db.query(WmTaskRolloverHistory).count()
        today_count = self.db.query(WmTaskRolloverHistory).filter(func.date(WmTaskRolloverHistory.changed_at) == today).count()
        critical_tasks = (
            self.db.query(WmTaskRolloverHistory.task_id)
            .group_by(WmTaskRolloverHistory.task_id)
            .having(func.count(WmTaskRolloverHistory.rollover_id) >= 3)
            .count()
        )
        employee_wise = (
            self.db.query(WmTaskRolloverHistory.changed_by, func.count(WmTaskRolloverHistory.rollover_id))
            .group_by(WmTaskRolloverHistory.changed_by)
            .all()
        )
        return {
            "total_rolled_over_tasks": total,
            "rolled_over_today": today_count,
            "critical_rollover_tasks": critical_tasks,
            "employee_wise_rollover_counts": [{"employee_id": eid, "count": c} for eid, c in employee_wise],
        }

    def escalation_digest_payload(self):
        ticket_groups = (
            self.db.query(WmTicket.company_id, WmTicket.branch_id, WmTicket.department_id, WmTicket.customer_id, WmTicket.priority, func.count(WmTicket.ticket_id))
            .filter(WmTicket.closed_at.is_(None))
            .group_by(WmTicket.company_id, WmTicket.branch_id, WmTicket.department_id, WmTicket.customer_id, WmTicket.priority)
            .all()
        )
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "groups": [
                {
                    "company_id": g[0],
                    "branch_id": g[1],
                    "department_id": g[2],
                    "client_id": g[3],
                    "priority": g[4],
                    "count": g[5],
                }
                for g in ticket_groups
            ],
            "near_breach": self.db.query(WmTicket).filter(WmTicket.response_sla_status == "NEARING_BREACH").count(),
            "breached": self.db.query(WmTicket).filter((WmTicket.response_sla_status == "BREACHED") | (WmTicket.closure_sla_status == "BREACHED")).count(),
            "high_priority_unresolved": self.db.query(WmTicket).filter(func.upper(WmTicket.priority) == "HIGH", WmTicket.closed_at.is_(None)).count(),
        }
