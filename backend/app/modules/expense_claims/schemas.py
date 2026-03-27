from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ExpenseClaimCreateRequest(BaseModel):
    claim_type: Literal["REIMBURSEMENT", "DIRECT_EXPENSE"]
    expense_type: str
    emp_id: int
    entered_for_emp_id: int | None = None
    job_id: int | None = None
    task_id: int | None = None
    task_participant_id: int | None = None
    timesheet_id: int | None = None
    expense_date: date
    amount: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    recoverable_flag: bool = False
    cost_center_id: int | None = None
    vendor_payee_name: str | None = None
    remarks: str | None = None
    receipt_attachment_ref: str | None = None
    submit_mode: str = Field(default="DRAFT", pattern="^(DRAFT|SUBMIT)$")


class ExpenseClaimCreateResponse(BaseModel):
    status: str
    claim_id: int
    claim_no: str
    approval_status: str
    message: str


class ExpenseClaimSubmitRequest(BaseModel):
    remarks: str | None = None


class ExpenseClaimSubmitResponse(BaseModel):
    status: str
    claim_id: int
    approval_status: str
    message: str


class ExpenseClaimDecisionRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    decision_note: str | None = None
    override_flag: bool = False
    override_reason: str | None = None


class ExpenseClaimDecisionResponse(BaseModel):
    status: str
    claim_id: int
    approval_status: str
    message: str


class ConvertExpenseClaimRequest(BaseModel):
    override_flag: bool = False
    override_reason: str | None = None


class ConvertExpenseClaimResponse(BaseModel):
    status: str
    claim_id: int
    voucher_id: int | None
    voucher_no: str | None
    conversion_status: str
    message: str
