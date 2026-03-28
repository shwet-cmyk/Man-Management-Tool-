from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta


@dataclass
class CalendarConfig:
    office_start: time = time(9, 0)
    office_end: time = time(18, 0)
    weekly_off_days: tuple[int, ...] = (5, 6)
    holidays: set[str] | None = None


class BusinessCalendarService:
    def __init__(self, config: CalendarConfig | None = None):
        self.config = config or CalendarConfig()

    def add_working_minutes(self, start_datetime: datetime, minutes: int):
        current = start_datetime
        remaining = max(minutes, 0)
        while remaining > 0:
            current += timedelta(minutes=1)
            if self._is_working_minute(current):
                remaining -= 1
        return current

    def add_working_days(self, start_datetime: datetime, days: int):
        return self.add_working_minutes(start_datetime, days * self._working_minutes_per_day())

    def calculate_elapsed_working_minutes(self, start_datetime: datetime, end_datetime: datetime):
        if end_datetime <= start_datetime:
            return 0
        current = start_datetime
        minutes = 0
        while current < end_datetime:
            current += timedelta(minutes=1)
            if self._is_working_minute(current):
                minutes += 1
        return minutes

    def calculate_remaining_working_minutes(self, now: datetime, due_datetime: datetime):
        if now >= due_datetime:
            return 0
        return self.calculate_elapsed_working_minutes(now, due_datetime)

    def _is_working_minute(self, dt: datetime):
        if dt.weekday() in self.config.weekly_off_days:
            return False
        if self.config.holidays and dt.date().isoformat() in self.config.holidays:
            return False
        return self.config.office_start <= dt.time() < self.config.office_end

    def _working_minutes_per_day(self):
        start = datetime.combine(datetime.utcnow().date(), self.config.office_start)
        end = datetime.combine(datetime.utcnow().date(), self.config.office_end)
        return int((end - start).total_seconds() // 60)
