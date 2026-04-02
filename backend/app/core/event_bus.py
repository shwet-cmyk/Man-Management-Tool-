from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

try:
    import redis
except Exception:  # pragma: no cover - optional runtime dep fallback
    redis = None


EVENT_LOG: list[dict[str, Any]] = []
_redis_client = None


def _client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if redis is None:
        return None
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        _redis_client = redis.Redis.from_url(url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = None
        return None


def publish_event(event_type: str, payload: dict[str, Any], channel: str = "tez.events") -> dict[str, Any]:
    event = {
        "event_type": event_type,
        "payload": payload,
        "channel": channel,
        "timestamp": datetime.utcnow().isoformat(),
    }
    EVENT_LOG.append(event)

    client = _client()
    if client:
        client.publish(channel, json.dumps(event))

    return event
