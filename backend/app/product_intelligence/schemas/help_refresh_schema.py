from __future__ import annotations

from pydantic import BaseModel, Field


class FeatureChangeInput(BaseModel):
    module_name: str
    screen_key: str
    route_path: str | None = None
    component_name: str | None = None
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    change_category: str | None = None


class HelpRefreshRunRequest(BaseModel):
    release_version: str = Field(min_length=1)
    release_title: str | None = None
    release_summary: str | None = None
    changes: list[FeatureChangeInput] = Field(default_factory=list)


class HelpRefreshLogResponse(BaseModel):
    help_refresh_id: int
    screen_key: str
    module_name: str
    refresh_mode: str
    refresh_status: str
