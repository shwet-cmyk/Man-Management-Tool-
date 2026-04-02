from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class ReleaseNoteResponse(BaseModel):
    release_note_id: int
    release_version: str
    release_title: str
    release_summary: str
    release_date: datetime
    release_type: str | None = None
