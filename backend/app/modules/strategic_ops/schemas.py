from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class GoalCreateRequest(BaseModel):
    goal_code: str
    goal_name: str
    goal_type: str
    description: str | None = None
    owner_id: int
    owner_name: str
    team_id: int | None = None
    company_id: int
    branch_id: int | None = None
    department_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "Draft"
    priority: str = "Medium"
    target_value: float | None = None
    current_value: float | None = None
    measurement_type: str | None = None
    update_mode: str = "Manual"
    risk_status: str = "On Track"
    parent_goal_id: int | None = None
    linked_metric_type: str | None = None
    created_by: int = 1


class GoalLinkRequest(BaseModel):
    linked_entity_type: Literal["PROJECT", "TASK", "JOB", "DASHBOARD", "KPI", "DEPARTMENT", "MANAGER", "CLIENT"]
    linked_entity_id: int
    linked_metric_type: str | None = None
    created_by: int = 1


class GoalProgressUpdateRequest(BaseModel):
    current_value: float
    progress_percent: float | None = None
    updated_by: int


class IntakeRequestCreate(BaseModel):
    request_code: str
    title: str
    description: str | None = None
    request_type: str
    source_type: str = "manual"
    form_template: str = "Project Request"
    client_id: int | None = None
    client_name: str | None = None
    company_id: int
    branch_id: int | None = None
    department_id: int | None = None
    category: str | None = None
    product_service: str | None = None
    urgency: str = "Medium"
    expected_due_date: date | None = None
    estimated_value: float | None = None
    requester_id: int
    requester_name: str
    approval_required: bool = False
    custom_fields: dict = Field(default_factory=dict)
    created_by: int = 1


class IntakeStatusUpdateRequest(BaseModel):
    status: str
    triage_owner_id: int | None = None
    triage_owner_name: str | None = None
    updated_by: int = 1


class IntakeConvertRequest(BaseModel):
    target_entity_type: Literal["Ticket", "Project", "Task", "Job"]
    target_entity_id: int
    updated_by: int = 1


class LaunchCreateRequest(BaseModel):
    launch_code: str
    launch_name: str
    product_id: int | None = None
    product_name: str | None = None
    launch_type: str
    launch_owner_id: int
    launch_manager_id: int | None = None
    client_id: int | None = None
    project_id: int | None = None
    start_date: date | None = None
    target_launch_date: date | None = None
    launch_priority: str = "Medium"
    budget_amount: float | None = None
    created_by: int = 1


class LaunchMilestoneRequest(BaseModel):
    phase_name: str
    milestone_name: str
    owner_id: int | None = None
    due_date: date | None = None


class LaunchStatusUpdateRequest(BaseModel):
    launch_status: str
    readiness_percent: float | None = None
    risk_status: str | None = None
    dependency_health: str | None = None
    updated_by: int


class ResourceAllocationRequest(BaseModel):
    employee_id: int
    employee_name: str
    manager_id: int | None = None
    department_id: int | None = None
    project_id: int | None = None
    launch_id: int | None = None
    linked_entity_type: Literal["TASK", "JOB", "PROJECT", "LAUNCH", "INTAKE"]
    linked_entity_id: int
    allocation_date: date
    planned_hours: float
    actual_hours: float = 0
    created_by: int = 1


class ResourceViewFilter(BaseModel):
    manager_id: int | None = None
    department_id: int | None = None
    company_id: int | None = None
    start_date: date
    end_date: date


class StrategicReportRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
