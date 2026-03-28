from pydantic import BaseModel, Field


class ApprovalStepRequest(BaseModel):
    step_order: int
    approver_type: str
    approver_id: int
    is_parallel: bool = False
    dependency_step_id: int | None = None
    condition: dict = Field(default_factory=dict)


class ApprovalRuleRequest(BaseModel):
    condition_type: str
    operator: str
    value: str
    field_name: str | None = None


class ApprovalWorkflowCreateRequest(BaseModel):
    module_name: str
    name: str
    is_active: bool = True
    steps: list[ApprovalStepRequest] = Field(default_factory=list)
    rules: list[ApprovalRuleRequest] = Field(default_factory=list)


class ApprovalSubmitRequest(BaseModel):
    module_name: str
    entity_type: str
    entity_id: int
    amount: float | None = None
    data: dict = Field(default_factory=dict)


class ApprovalActionRequest(BaseModel):
    transaction_id: int
    user_id: int
    action: str
    remarks: str | None = None
