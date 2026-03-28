from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EmployeeGroupCreateRequest(BaseModel):
    group_code: str
    group_name: str
    description: str | None = None
    active_flag: bool = True
    employee_ids: list[int] = []
    created_by: int = 1


class HolidayCreateRequest(BaseModel):
    holiday_name: str
    holiday_date: date
    holiday_type: str = "General"
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    calendar_type: str = "Company"
    remarks: str | None = None
    active_flag: bool = True
    created_by: int = 1


class JobUpsertRequest(BaseModel):
    job_name: str
    client_id: int | None = None
    client_name: str | None = None
    service_id: int | None = None
    service_name: str | None = None
    priority: str = "Medium"
    company_id: int
    branch_id: int | None = None
    department_id: int | None = None
    start_date: date
    due_date: date
    amount: Decimal = Decimal("0")
    billable_flag: bool = False
    expected_hours: Decimal = Decimal("0")
    expected_minutes: int = 0
    manager_id: int | None = None
    manager_name: str | None = None
    assigned_employee_id: int
    assigned_employee_name: str | None = None
    remarks: str | None = None
    parent_task_id: int | None = None
    created_by: int = 1


class JobTaskLineRequest(BaseModel):
    parent_job_id: int
    task_name: str
    description: str | None = None
    assigned_employee_id: int | None = None
    planned_start_date: date | None = None
    planned_due_date: date | None = None
    priority: str | None = None
    remarks: str | None = None
    sequence_no: int | None = None
    dependency_task_id: int | None = None
    mandatory_flag: bool = True
    created_by: int = 1


class JobTaskStatusRequest(BaseModel):
    status: str = Field(pattern="^(Pending|In Progress|Completed|Cancelled)$")
    updated_by: int = 1


class TimesheetEntryRequest(BaseModel):
    job_id: int
    job_task_id: int | None = None
    employee_id: int
    date: date
    start_time: datetime | None = None
    end_time: datetime | None = None
    spent_hours: Decimal = Decimal("0")
    spent_minutes: int = 0
    remarks: str | None = None
    manager_id: int | None = None
    expense_lines: list[dict] = []
    reimbursement_lines: list[dict] = []
    created_by: int = 1


class ApprovalActionRequest(BaseModel):
    entity_type: str
    entity_id: int
    approval_type: str
    action: str = Field(pattern="^(REQUEST|APPROVE|REJECT|RETURN)$")
    user_id: int
    remarks: str | None = None


class BillingActionRequest(BaseModel):
    job_id: int
    billed_amount: Decimal
    billed_by: int


class SettingsUpsertRequest(BaseModel):
    company_id: int | None = None
    timesheet_mandatory_for_completion: bool = True
    mandatory_task_completion_for_billing: bool = True
    manager_approval_mandatory_for_timesheet: bool = False
    job_completion_approval_required: bool = False
    max_attachment_size_mb: int = 10
    allowed_attachment_types: str = "pdf,jpg,jpeg,png"
    overtime_allowed: bool = True
    multiple_timesheets_per_day: bool = True
    billable_amount_editable_after_completion: bool = False
    delete_allowed_after_timesheet_entry: bool = False
    expense_approval_required: bool = False
    reimbursement_approval_required: bool = False
    updated_by: int = 1
