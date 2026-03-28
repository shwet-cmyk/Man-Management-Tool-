from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    client_name: str
    api_key: str
    rate_limit_per_minute: int = 1000


class WebhookCreateRequest(BaseModel):
    event_name: str
    url: str
    secret: str | None = None


class IntegrationTaskCreateRequest(BaseModel):
    company_id: int
    job_id: int
    title: str
    assigned_users: list[int] = Field(default_factory=list)
    deadline: datetime
    created_by: int


class IntegrationTaskUpdateRequest(BaseModel):
    title: str | None = None
    status_code: str | None = None
    manager_emp_id: int | None = None


class IntegrationTimesheetPushRequest(BaseModel):
    company_id: int
    job_id: int
    task_id: int | None = None
    emp_id: int
    work_date: date
    hours: Decimal
    billable_hours: Decimal = Decimal("0")
    created_by: int


class IntegrationExpensePushRequest(BaseModel):
    company_id: int
    emp_id: int
    expense_date: date
    amount: Decimal
    tax_amount: Decimal = Decimal("0")
    expense_type: str
    created_by: int
    job_id: int | None = None
    task_id: int | None = None


class TransactionPushRequest(BaseModel):
    source: Literal["INVOICE", "PAYMENT", "JOURNAL", "TASK_LOG"]
    reference_no: str
    payload: dict
