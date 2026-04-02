from __future__ import annotations
from datetime import datetime

class IdleComputationService:
    def compute_idle_minutes(self, events: list[dict], idle_threshold_minutes: int) -> int:
        input_events = [e for e in events if (e.get('event_type') or '').upper() == 'USER_INPUT']
        if len(input_events) < 2:
            return 0
        idle = 0
        sorted_events = sorted(input_events, key=lambda x: x['event_timestamp'])
        for i in range(1, len(sorted_events)):
            prev: datetime = sorted_events[i-1]['event_timestamp']
            curr: datetime = sorted_events[i]['event_timestamp']
            gap = (curr - prev).total_seconds() / 60
            if gap > idle_threshold_minutes:
                idle += int(gap - idle_threshold_minutes)
        return idle
