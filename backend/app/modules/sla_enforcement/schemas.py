from pydantic import BaseModel, Field


class SlaStartRequestV2(BaseModel):
    ticket_id: str
    priority: str = Field(pattern="^(HIGH|LOW|CUSTOM)$")
    created_at: str
    timezone: str = "UTC"


class SlaPauseRequest(BaseModel):
    sla_id: str
    paused: bool
    reason: str | None = None


class SlaStatusResponse(BaseModel):
    sla_deadline: str
    status: str
