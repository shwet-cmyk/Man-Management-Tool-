from typing import Literal

from pydantic import BaseModel


PredictionType = Literal["DELAY", "COST", "COMPLETION"]


class GenerateInsightRequest(BaseModel):
    entity_type: Literal["TASK", "JOB"]
    entity_id: int


class ApplyRecommendationRequest(BaseModel):
    rec_id: int
    applied_by: int
