from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

RecommendationStatus = Literal['NEW', 'UNDER_REVIEW', 'ACCEPTED', 'REJECTED', 'IMPLEMENTED']


class AiRecommendationResponse(BaseModel):
    recommendation_id: int
    module_name: str
    screen_key: str | None = None
    recommendation_title: str
    recommendation_text: str
    evidence_summary: str | None = None
    confidence_score: float | None = None
    severity_level: str | None = None
    status: RecommendationStatus


class AiRecommendationStatusUpdate(BaseModel):
    status: RecommendationStatus
