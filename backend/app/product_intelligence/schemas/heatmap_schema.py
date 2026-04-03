from __future__ import annotations
from pydantic import BaseModel

class HeatmapPoint(BaseModel):
    screen_key: str
    route_path: str
    element_id: str | None
    heatmap_type: str
    interaction_count: int
