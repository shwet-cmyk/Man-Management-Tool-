from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class ActivityEventRequest(BaseModel):
    event_type: str
    event_timestamp: datetime
    active_app_name: str | None = None
    active_executable: str | None = None
    active_window_title: str | None = None
    active_domain: str | None = None
    active_url: str | None = None
    input_source: str | None = None
    duration_seconds: int | None = None
    metadata_json: str | None = None

class AgentSyncRequest(BaseModel):
    device_id: int
    user_id: int
    events: list[ActivityEventRequest]

class AgentHeartbeatRequest(BaseModel):
    device_id: int
    user_id: int
    heartbeat_at: datetime

class AgentSyncResponse(BaseModel):
    success: bool
    processed_count: int
    breach_count: int
    warnings: list[str]
