from __future__ import annotations
from pydantic import BaseModel

class HelpRefreshRunRequest(BaseModel):
    release_version: str

class HelpRefreshLogResponse(BaseModel):
    help_refresh_id: int
    screen_key: str
    module_name: str
    refresh_mode: str
    refresh_status: str
