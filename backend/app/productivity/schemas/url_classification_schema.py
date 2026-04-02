from __future__ import annotations
from pydantic import BaseModel

class UrlClassificationUpsertRequest(BaseModel):
    domain_name: str
    url_pattern: str | None = None
    browser_scope: str | None = None
    classification_type: str
    notes: str | None = None

class UrlClassificationResponse(BaseModel):
    url_classification_id: int
    domain_name: str
    classification_type: str
