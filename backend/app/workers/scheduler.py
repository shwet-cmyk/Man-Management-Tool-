from __future__ import annotations

import asyncio
from datetime import datetime

from app.core.event_bus import publish_event


async def run_periodic_jobs(stop_event: asyncio.Event):
    while not stop_event.is_set():
        publish_event("SLA_CHECK_TICK", {"at": datetime.utcnow().isoformat()})
        publish_event("NOTIFICATION_SWEEP_TICK", {"at": datetime.utcnow().isoformat()})
        publish_event("APPROVAL_ESCALATION_TICK", {"at": datetime.utcnow().isoformat()})
        publish_event("GAMIFICATION_RECALC_TICK", {"at": datetime.utcnow().isoformat()})
        await asyncio.sleep(300)
