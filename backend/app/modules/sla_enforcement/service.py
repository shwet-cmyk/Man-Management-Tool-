from __future__ import annotations

from datetime import datetime, timedelta

from app.models.sla_tracking import SlaTracking


class SlaEnforcementService:
    def __init__(self, db):
        self.db = db

    def start_tracking(self, ticket_id: str, priority: str, created_at: str, timezone: str = "UTC"):
        start = datetime.fromisoformat(created_at)
        deadline = self.calculate_sla(priority=priority, start_date=start)
        row = SlaTracking(ticket_id=ticket_id, priority=priority, start_time=start, deadline=deadline, status="ACTIVE", timezone=timezone)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"sla_id": row.id, "sla_deadline": row.deadline, "status": "WITHIN_SLA"}

    def get_status(self, sla_id: str):
        row = self.db.query(SlaTracking).filter(SlaTracking.id == sla_id).first()
        if not row:
            return {"status": "NOT_FOUND"}

        status = "BREACHED" if datetime.utcnow() > row.deadline and row.status == "ACTIVE" else "WITHIN_SLA"
        return {"sla_deadline": row.deadline, "status": status, "escalation_level": row.escalation_level}

    def monitor_and_escalate(self):
        now = datetime.utcnow()
        breached = 0
        rows = self.db.query(SlaTracking).filter(SlaTracking.status == "ACTIVE", SlaTracking.paused == 0).all()
        for row in rows:
            if now > row.deadline:
                row.status = "BREACHED"
                row.escalation_level += 1
                breached += 1
        self.db.commit()
        return {"breached": breached}

    def pause_resume(self, sla_id: str, paused: bool, reason: str | None):
        row = self.db.query(SlaTracking).filter(SlaTracking.id == sla_id).first()
        if not row:
            return {"status": "NOT_FOUND"}
        row.paused = 1 if paused else 0
        row.pause_reason = reason if paused else None
        self.db.commit()
        return {"status": "PAUSED" if paused else "ACTIVE", "sla_id": row.id}

    def calculate_sla(self, priority: str, start_date: datetime):
        deadline = start_date
        if priority == "HIGH":
            return deadline + timedelta(hours=24)
        if priority == "LOW":
            return self.add_working_days(deadline, 3)
        return self.add_working_days(deadline, 2)

    def add_working_days(self, date: datetime, days: int):
        result = date
        added = 0
        while added < days:
            result = result + timedelta(days=1)
            if result.weekday() < 5:
                added += 1
        return result
