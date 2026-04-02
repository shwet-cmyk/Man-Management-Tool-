from __future__ import annotations
from datetime import date
from pydantic import BaseModel

class DailySummaryResponse(BaseModel):
    summary_date: date
    user_id: int
    present_minutes: int
    active_minutes: int
    productive_minutes: int
    neutral_minutes: int
    unproductive_minutes: int
    idle_minutes: int
    locked_minutes: int
    hibernate_minutes: int
    offline_minutes: int
    shutdown_count: int
    reboot_count: int
    productivity_status: str

class TeamSummaryRecord(BaseModel):
    user_id: int
    employee_name: str
    productive_minutes: int
    idle_minutes: int
    status: str
