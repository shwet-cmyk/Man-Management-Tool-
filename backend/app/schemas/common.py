from datetime import datetime
from pydantic import BaseModel, Field


class AuditMeta(BaseModel):
    changed_by: str = "system"
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    reason: str | None = None


class StandardResponse(BaseModel):
    status: str = "success"
    message: str
