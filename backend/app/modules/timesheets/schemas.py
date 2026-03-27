from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from typing import Literal


class TimesheetCreateRequest(BaseModel):
    emp_id: int
    job_id: int
    task_id: int | None = None
    task_participant_id: int | None = None
    work_date: date
    start_time: datetime | None = None
    end_time: datetime | None = None
    hours: Decimal
    billable_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    activity_type: str | None = None
    remarks: str | None = None
    attachment_ref: str | None = None
    expense_link_id: int | None = None
    reimbursement_link_id: int | None = None
    submit_mode: str = Field(default="DRAFT", pattern="^(DRAFT|SUBMIT)$")
    entered_for_emp_id: int | None = None
    override_participant_mapping: bool = False


class TimesheetCreateResponse(BaseModel):
    status: str
    timesheet_id: int
    approval_status: str
    participant_status_hint: str | None = None
    message: str


class TimesheetSubmitRequest(BaseModel):
    remarks: str | None = None


class TimesheetSubmitResponse(BaseModel):
    status: str
    timesheet_id: int
    approval_status: str
    message: str


class TimesheetDecisionRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    decision_note: str | None = None
    override_flag: bool = False
    override_reason: str | None = None


class TimesheetDecisionResponse(BaseModel):
    status: str
    timesheet_id: int
    approval_status: str
    message: str
