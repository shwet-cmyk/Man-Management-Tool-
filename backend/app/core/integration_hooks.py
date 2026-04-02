from __future__ import annotations

from typing import Any

from app.core.event_bus import publish_event


def emit_audit_event(action: str, payload: dict[str, Any]) -> None:
    publish_event("audit.log", {"action": action, **payload}, channel="tez.audit")


def emit_notification_event(topic: str, payload: dict[str, Any]) -> None:
    publish_event("notification.dispatch", {"topic": topic, **payload}, channel="tez.notifications")
