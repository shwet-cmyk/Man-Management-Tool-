from __future__ import annotations
from pydantic import BaseModel

class AppClassificationUpsertRequest(BaseModel):
    app_name: str
    executable_name: str | None = None
    app_category: str | None = None
    classification_type: str
    notes: str | None = None

class AppClassificationResponse(BaseModel):
    app_classification_id: int
    app_name: str
    classification_type: str
