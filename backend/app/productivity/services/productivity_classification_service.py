from __future__ import annotations

def classify_status(productive_minutes: int, policy: dict) -> str:
    productive_hours = productive_minutes / 60
    if productive_hours >= float(policy['productive_target_hours']):
        return 'PRODUCTIVE'
    if productive_hours >= float(policy['borderline_lower_hours']):
        return 'BORDERLINE'
    return 'UNDERPRODUCTIVE'
