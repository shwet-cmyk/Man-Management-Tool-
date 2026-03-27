from datetime import datetime

from pydantic import BaseModel, Field


class LeadCreateRequest(BaseModel):
    name: str
    source: str
    assigned_users: list[int] = Field(default_factory=list)
    estimated_value: int | None = None


class FollowupCreateRequest(BaseModel):
    entity_type: str
    entity_id: int
    next_followup_date: datetime
    remarks: str | None = None
    assigned_to: int


class DealCreateRequest(BaseModel):
    opportunity_id: int
    negotiated_value: int
    customer_name: str | None = None


class DealInvoiceRequest(BaseModel):
    approved_by: int
    push_to_tez: bool = False


class LifecycleUpdateRequest(BaseModel):
    customer_id: int
    stage: str
    churn_risk_score: int = 0
