from __future__ import annotations
from datetime import datetime, timedelta, UTC

def raw_retention_cutoff(days: int = 90) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)
