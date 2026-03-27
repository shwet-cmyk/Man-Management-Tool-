from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class BillingConfigureRequest(BaseModel):
    entity_type: Literal["JOB", "TASK"]
    job_id: int | None = None
    task_id: int | None = None
    customer_id: int
    billable_flag: bool
    billing_model: Literal["NON_BILLABLE", "TIME_MATERIAL", "FIXED_FEE", "MILESTONE", "RETAINER"]
    fixed_billing_amount: Decimal | None = None
    billing_remarks: str | None = None


class BillingConfigureResponse(BaseModel):
    status: str
    entity_type: str
    billing_status: str
    message: str


class MarkReadyForBillingRequest(BaseModel):
    entity_type: Literal["JOB", "TASK"]
    job_id: int | None = None
    task_id: int | None = None
    billing_remarks: str | None = None


class MarkReadyForBillingResponse(BaseModel):
    status: str
    entity_type: str
    billing_status: str
    included_billable_hours: Decimal
    included_recoverable_expense: Decimal
    message: str


class RemoveReadinessRequest(BaseModel):
    entity_type: Literal["JOB", "TASK"]
    job_id: int | None = None
    task_id: int | None = None
    billing_remarks: str | None = None


class RemoveReadinessResponse(BaseModel):
    status: str
    entity_type: str
    billing_status: str
    message: str


class ProformaRequest(BaseModel):
    entity_type: Literal["JOB", "TASK"]
    job_id: int | None = None
    task_id: int | None = None
    action_type: Literal["CREATE", "LINK_EXISTING"]
    proforma_id: int | None = None
    proforma_no: str | None = None
    billing_remarks: str | None = None


class ProformaResponse(BaseModel):
    status: str
    entity_type: str
    proforma_no: str
    billing_status: str
    message: str


class InvoiceRequest(BaseModel):
    entity_type: Literal["JOB", "TASK"]
    job_id: int | None = None
    task_id: int | None = None
    action_type: Literal["CREATE", "LINK_EXISTING"]
    invoice_id: int | None = None
    invoice_no: str | None = None
    billed_amount: Decimal | None = None
    billed_date: date | None = None
    billing_remarks: str | None = None


class InvoiceResponse(BaseModel):
    status: str
    entity_type: str
    invoice_no: str
    billing_status: str
    remaining_unbilled_amount: Decimal
    message: str
