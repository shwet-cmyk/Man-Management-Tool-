from pydantic import BaseModel, Field


class WorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    module: str
    trigger_event: str
    is_active: bool = True


class WorkflowUpdateRequest(BaseModel):
    name: str | None = None
    module: str | None = None
    trigger_event: str | None = None
    is_active: bool | None = None


class WorkflowNodeRequest(BaseModel):
    node_type: str
    name: str
    sequence_no: int = 1
    config: dict = Field(default_factory=dict)


class WorkflowEdgeRequest(BaseModel):
    from_node_id: int
    to_node_id: int
    edge_condition: str | None = None


class TriggerWorkflowRequest(BaseModel):
    module: str
    event_name: str
    entity_type: str
    entity_id: int
    context: dict = Field(default_factory=dict)


class WorkflowApprovalDecisionRequest(BaseModel):
    approval_id: int
    decided_by: int
    remarks: str | None = None


class SlaControlRequest(BaseModel):
    instance_id: int
