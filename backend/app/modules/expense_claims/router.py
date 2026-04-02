from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.expense_claims.schemas import (
    ExpenseClaimCreateRequest,
    ExpenseClaimCreateResponse,
    ConvertExpenseClaimRequest,
    ConvertExpenseClaimResponse,
    ExpenseClaimDecisionRequest,
    ExpenseClaimDecisionResponse,
    ExpenseClaimSubmitRequest,
    ExpenseClaimSubmitResponse,
)
from app.modules.expense_claims.service import ExpenseClaimService

router = APIRouter(prefix="/wm/expense-claims", tags=["Work Management - Expense Claims"])


@router.post("", response_model=ExpenseClaimCreateResponse)
def create_expense_claim(payload: ExpenseClaimCreateRequest, db: Session = Depends(get_db)):
    return ExpenseClaimService(db).create_claim(payload)


@router.post("/{claim_id}/submit", response_model=ExpenseClaimSubmitResponse)
def submit_expense_claim(claim_id: int, payload: ExpenseClaimSubmitRequest, db: Session = Depends(get_db)):
    return ExpenseClaimService(db).submit_claim(claim_id=claim_id, remarks=payload.remarks)


@router.post("/{claim_id}/decision", response_model=ExpenseClaimDecisionResponse)
def decide_expense_claim(claim_id: int, payload: ExpenseClaimDecisionRequest, db: Session = Depends(get_db)):
    return ExpenseClaimService(db).decide_claim(claim_id=claim_id, payload=payload)


@router.post("/{claim_id}/convert-to-voucher", response_model=ConvertExpenseClaimResponse)
def convert_to_voucher(claim_id: int, payload: ConvertExpenseClaimRequest, db: Session = Depends(get_db)):
    return ExpenseClaimService(db).convert_to_voucher(claim_id=claim_id, payload=payload)
