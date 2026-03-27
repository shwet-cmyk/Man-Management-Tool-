from pydantic import BaseModel, Field


class SlaRuleCreateRequest(BaseModel):
    module: str
    condition: dict = Field(default_factory=dict)
    response_time: int
    resolution_time: int
    unit: str = "minutes"
    escalation_config: dict
    company_id: int | None = None
    branch_id: int | None = None


class SlaStartRequest(BaseModel):
    module: str
    entity_type: str
    entity_id: int
    assignee_user_id: int | None = None
    company_id: int | None = None
    branch_id: int | None = None
    context: dict = Field(default_factory=dict)


class SlaControlRequest(BaseModel):
    sla_instance_id: int


class SlaEscalateRequest(BaseModel):
    sla_instance_id: int


class HolidayCreateRequest(BaseModel):
    holiday_date: str
    name: str
    company_id: int | None = None
    branch_id: int | None = None
