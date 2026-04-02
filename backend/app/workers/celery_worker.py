from __future__ import annotations

import os

from celery import Celery

from app.core.event_bus import publish_event

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
app = Celery("tez-worker", broker=redis_url, backend=redis_url)

app.conf.beat_schedule = {
    "sla-check-every-5-min": {"task": "app.workers.celery_worker.sla_checks", "schedule": 300.0},
    "notification-drain": {"task": "app.workers.celery_worker.notification_triggers", "schedule": 120.0},
    "gamification-calc": {"task": "app.workers.celery_worker.gamification_calc", "schedule": 600.0},
}


@app.task
def sla_checks():
    publish_event("SLA_BREACHED", {"source": "celery", "message": "periodic sla check tick"})
    return "sla-check-done"


@app.task
def notification_triggers():
    publish_event("NOTIFICATION_TRIGGER", {"source": "celery"})
    return "notifications-triggered"


@app.task
def escalation_jobs():
    publish_event("ESCALATION_TRIGGER", {"source": "celery"})
    return "escalation-triggered"


@app.task
def gamification_calc():
    publish_event("GAMIFICATION_RECALCULATE", {"source": "celery"})
    return "gamification-recalculated"
