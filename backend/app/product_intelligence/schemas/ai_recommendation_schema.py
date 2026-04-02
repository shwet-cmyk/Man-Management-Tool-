from __future__ import annotations
from pydantic import BaseModel

class AiRecommendationResponse(BaseModel):
    recommendation_id: int
    module_name: str
    screen_key: str | None = None
    recommendation_title: str
    recommendation_text: str
    evidence_summary: str | None = None
    confidence_score: float | None = None
    severity_level: str | None = None
    status: str

class AiRecommendationStatusUpdate(BaseModel):
    status: str
