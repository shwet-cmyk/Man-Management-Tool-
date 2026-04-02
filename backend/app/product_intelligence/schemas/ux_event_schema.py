from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class UxEvent(BaseModel):
    route_path: str
    screen_key: str
    module_name: str
    element_id: str | None = None
    element_label: str | None = None
    event_type: str
    event_timestamp: datetime
    metadata: dict | None = None

class UxEventIngestRequest(BaseModel):
    session_id: str
    user_id: int = 1
    role_id: int | None = None
    events: list[UxEvent]

class UxIngestResponse(BaseModel):
    success: bool
    ingested_count: int
    dead_click_count: int
    rage_click_count: int
