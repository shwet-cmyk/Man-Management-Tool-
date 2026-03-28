from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.modules.tickets.business_calendar_service import BusinessCalendarService


@dataclass
class SlaRule:
    response_minutes: int | None
    closure_minutes: int
    nearing_breach_threshold_minutes: int


DEFAULT_RULES = {
    "HIGH": SlaRule(response_minutes=24 * 60, closure_minutes=24 * 60, nearing_breach_threshold_minutes=120),
    "MEDIUM": SlaRule(response_minutes=24 * 60, closure_minutes=3 * 9 * 60, nearing_breach_threshold_minutes=180),
    "LOW": SlaRule(response_minutes=24 * 60, closure_minutes=3 * 9 * 60, nearing_breach_threshold_minutes=180),
}


class SlaEngine:
    def __init__(self, calendar: BusinessCalendarService):
        self.calendar = calendar

    def due_times(self, created_on: datetime, priority: str):
        rule = DEFAULT_RULES[priority.upper()]
        response_due = self.calendar.add_working_minutes(created_on, rule.response_minutes) if rule.response_minutes else None
        closure_due = self.calendar.add_working_minutes(created_on, rule.closure_minutes)
        return response_due, closure_due

    def compute_status(self, done_at: datetime | None, due_at: datetime | None, now: datetime):
        if not due_at:
            return "PENDING", 0
        if done_at:
            delay = max(0, self.calendar.calculate_elapsed_working_minutes(due_at, done_at)) if done_at > due_at else 0
            return ("MET" if done_at <= due_at else "BREACHED"), delay

        remaining = self.calendar.calculate_remaining_working_minutes(now, due_at)
        if now > due_at:
            return "BREACHED", self.calendar.calculate_elapsed_working_minutes(due_at, now)
        if remaining <= 120:
            return "NEARING_BREACH", 0
        return "ON_TRACK", 0
