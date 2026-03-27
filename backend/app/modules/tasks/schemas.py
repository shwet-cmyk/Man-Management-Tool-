from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from typing import Literal


class TaskCreateRequest(BaseModel):
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    customer_id: int | None = None
    project_id: int | None = None
    cost_center_id: int | None = None

    title: str = Field(default="", max_length=500)
    description: str | None = None
    task_type: str = "Task"
    priority_code: str = "Medium"

    primary_owner_emp_id: int | None = None
    contributor_emp_ids: list[int] = Field(default_factory=list)
    manager_emp_id: int | None = None
    reviewer_emp_id: int | None = None

    billable_flag: bool | None = None
    billed_amount: Decimal = Decimal("0")
    estimated_hours: Decimal | None = None
    planned_start: datetime | None = None
    due_at: datetime | None = None

    workflow_id: int | None = None
    tags: list[str] = Field(default_factory=list)

    save_mode: str = Field(default="SUBMIT", pattern="^(SUBMIT|DRAFT)$")
    source_type: str = Field(default="MANUAL", pattern="^(MANUAL|API|WORKFLOW|RECURRING|SYSTEM)$")
    source_reference: str | None = None
    allow_duplicate: bool = False


class TaskAssignRequest(BaseModel):
    primary_owner_emp_id: int
    contributors: list[int] = Field(default_factory=list)
    reviewer_emp_id: int | None = None
    manager_emp_id: int | None = None
    watchers: list[int] = Field(default_factory=list)
    keep_previous_owner_as_contributor: bool = True


class TaskAssignBulkRequest(BaseModel):
    task_ids: list[int]
    assignment: TaskAssignRequest


class TaskStatusTransitionRequest(BaseModel):
    new_status: str
    action_code: str | None = None
    remarks: str | None = None
    changed_by: int = 1
    source: str = Field(default="UI", pattern="^(UI|API|SYSTEM|WORKFLOW)$")


class TaskStatusBulkRequest(BaseModel):
    task_ids: list[int]
    transition: TaskStatusTransitionRequest


class ChildItemCreateRequest(BaseModel):
    item_type: str = Field(pattern="^(SUBTASK|CHECKLIST|TODO)$")
    title: str = Field(max_length=500)
    description: str | None = None
    assignee_emp_id: int | None = None
    due_at: datetime | None = None
    priority_code: str | None = None
    estimated_hours: Decimal | None = None
    sequence_no: int | None = None
    source_type: str = Field(default="MANUAL", pattern="^(MANUAL|TEMPLATE|WORKFLOW|RECURRING|SYSTEM)$")


class ChildItemBulkCreateRequest(BaseModel):
    items: list[ChildItemCreateRequest]


class ChildItemStatusRequest(BaseModel):
    status_code: str = Field(pattern="^(Open|In Progress|Done|Cancelled)$")
    updated_by: int = 1


class ChildItemReorderRequest(BaseModel):
    item_orders: list[dict]
    updated_by: int = 1


class ChildItemResponse(BaseModel):
    status: str
    child_item_id: int
    parent_task_id: int
    item_type: str
    message: str


class ChildItemRead(BaseModel):
    child_item_id: int
    parent_task_id: int
    item_type: str
    title: str
    status_code: str
    assignee_emp_id: int | None
    due_at: datetime | None
    priority_code: str | None
    estimated_hours: Decimal | None
    sequence_no: int | None

    class Config:
        from_attributes = True


class TaskCreateResponse(BaseModel):
    status: str
    task_id: int
    task_no: str
    workflow_state: str
    message: str


class TaskAssignResponse(BaseModel):
    status: str
    message: str
    task_id: int


class TaskParticipantInput(BaseModel):
    emp_id: int
    role_code: Literal["OWNER", "EXECUTOR", "CONTRIBUTOR", "REVIEWER", "APPROVER", "WATCHER", "DEPENDENT_EXECUTOR"]
    planned_start: datetime
    planned_due: datetime
    sequence_no: int | None = None
    predecessor_sequence_no: int | None = None
    dependency_type: Literal["NONE", "FINISH_TO_START", "START_TO_START", "FINISH_TO_FINISH", "ACCEPTANCE_BASED"] = "NONE"
    submission_required: bool = False
    acceptance_required: bool = False
    allocation_pct: Decimal | None = None
    is_mandatory: bool = True
    remarks: str | None = None


class TaskParticipantsRequest(BaseModel):
    participants: list[TaskParticipantInput] = Field(default_factory=list)


class TaskParticipantsResponse(BaseModel):
    status: str
    task_id: int
    participant_count: int
    task_start_date: datetime
    task_due_date: datetime
    message: str


class ParticipantSubmitRequest(BaseModel):
    submission_note: str | None = None
    deliverable_link: str | None = None
    attachment_ref: str | None = None
    completion_pct: Decimal | None = None
    acceptance_required: bool | None = None
    remarks: str | None = None


class ParticipantSubmitResponse(BaseModel):
    status: str
    submission_id: int
    task_id: int
    participant_id: int
    participant_status: str
    handoff_status: str
    message: str


class SubmissionDecisionRequest(BaseModel):
    decision: Literal["ACCEPT", "REJECT"]
    decision_note: str | None = None
    override_flag: bool = False
    override_reason: str | None = None


class SubmissionDecisionResponse(BaseModel):
    status: str
    submission_id: int
    decision: str
    handoff_status: str
    predecessor_status: str
    message: str


class TaskStatusTransitionResponse(BaseModel):
    status: str
    task_id: int
    old_status: str
    new_status: str
    completed_at: datetime | None
    message: str


class TaskRead(BaseModel):
    task_id: int
    task_no: str
    title: str
    priority_code: str
    status_code: str
    primary_owner_emp_id: int
    manager_emp_id: int | None
    billable_flag: bool
    billed_amount: Decimal
    estimated_hours: Decimal
    planned_start: datetime
    due_at: datetime

    class Config:
        from_attributes = True
