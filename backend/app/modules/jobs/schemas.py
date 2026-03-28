from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TaskShellCreateRequest(BaseModel):
    company_id: int
    branch_id: int | None = None
    department_id: int | None = None
    client_id: int | None = None
    client_name: str | None = None
    title: str
    description: str | None = None
    product: str | None = None
    category: str | None = None
    priority: str = "Medium"
    billable_flag: bool = False
    billed_amount: Decimal = Decimal("0")
    task_owner_id: int
    task_owner_name: str | None = None
    manager_id: int | None = None
    manager_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    planned_hours: Decimal | None = None
    source_type: str = Field(default="MANUAL", pattern="^(MANUAL|TICKET|INTERNAL|API|SYSTEM)$")
    source_ticket_id: int | None = None
    remarks: str | None = None


class JobCreateRequest(BaseModel):
    parent_task_id: int
    title: str
    description: str | None = None
    assigned_employee_id: int
    assigned_employee_name: str | None = None
    assigned_manager_id: int | None = None
    assigned_manager_name: str | None = None
    company_id: int
    branch_id: int | None = None
    department_id: int | None = None
    client_id: int | None = None
    client_name: str | None = None
    priority: str = "Medium"
    start_date: date | None = None
    due_date: date | None = None
    planned_hours: Decimal | None = None
    estimated_amount: Decimal | None = None
    billable_flag: bool | None = None
    billed_amount: Decimal = Decimal("0")
    dependency_job_id: int | None = None
    dependency_mode: str = Field(default="FINISH_TO_START", pattern="^(FINISH_TO_START|FINISH_TO_FINISH)$")
    dependency_completion_required: bool = True
    transfer_required: bool = True
    acceptance_required: bool = True
    remarks: str | None = None


class JobStatusTransitionRequest(BaseModel):
    status: str = Field(pattern="^(Draft|Blocked|Awaiting Acceptance|Ready to Start|In Progress|Submitted|Completed|Reviewed|Billed|Closed|Reopened|Critical|Cancelled)$")
    changed_by: int = 1
    remarks: str | None = None


class TransferDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(ACCEPT|REJECT)$")
    employee_id: int
    reason: str | None = None


class GovernanceConfigRequest(BaseModel):
    monthly_working_hours: Decimal = Decimal("208")
    strict_shift_enforcement: bool = False


class DashboardScope(BaseModel):
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    manager_id: int | None = None
