from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


AnalyticsEntityType = Literal["JOB", "TASK", "CUSTOMER", "EMPLOYEE", "PARTICIPANT", "BRANCH", "DEPARTMENT", "COMPANY"]
ExceptionType = Literal[
    "ROLLED_OVER",
    "OVERRUN",
    "LATE_COMPLETION",
    "UNMANAGED",
    "NO_TIMESHEET",
    "STALE_WORK",
    "BLOCKED_DEPENDENCY",
    "LOST_WORK",
    "UNBILLED_READY",
    "UNDERBILLED",
    "BILLED_BELOW_COST",
    "APPROVAL_DELAY",
    "REPEATED_REWORK",
    "MISSING_OWNER",
    "MISSING_MANAGER",
    "MISSING_COST_RATE",
]


class ProfitabilityItem(BaseModel):
    entity_type: str
    entity_id: int
    entity_name: str
    approved_labor_hours: Decimal
    approved_billable_hours: Decimal
    labor_cost: Decimal
    non_labor_cost: Decimal
    total_cost: Decimal
    billed_amount: Decimal
    unbilled_amount: Decimal
    underbilling_amount: Decimal
    profit_amount: Decimal
    margin_percent: Decimal | None = None
    exception_type: str = ""


class ExceptionItem(BaseModel):
    exception_type: str
    severity: str
    entity_type: str
    entity_id: int
    entity_name: str | None = None
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    customer_id: int | None = None
    job_id: int | None = None
    task_id: int | None = None
    task_participant_id: int | None = None
    emp_id: int | None = None
    manager_id: int | None = None
    planned_due: datetime | None = None
    planned_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    billed_amount: Decimal | None = None
    total_cost: Decimal | None = None
    days_delayed: int | None = None
    exception_age_days: int | None = None
    exception_message: str


class RefreshExceptionsRequest(BaseModel):
    company_id: int | None = None
    entity_scope: Literal["ALL", "TASK", "PARTICIPANT", "BILLING", "APPROVAL"] = "ALL"


class RefreshExceptionsResponse(BaseModel):
    status: str
    exceptions_generated: int
    message: str


class ExceptionListResponse(BaseModel):
    items: list[ExceptionItem]
    totals: dict[str, int]


class ExceptionQueueFilter(BaseModel):
    exception_type: ExceptionType | None = None
    entity_type: Literal["JOB", "TASK", "PARTICIPANT", "TIMESHEET", "EXPENSE_CLAIM", "CUSTOMER"] | None = None
    company_id: int | None = None
    manager_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None


class AnalyticsQueryRequest(BaseModel):
    dimensions: list[str]
    metrics: list[str]
    filters: dict = {}


class AnalyticsReportRequest(BaseModel):
    name: str
    query: AnalyticsQueryRequest
