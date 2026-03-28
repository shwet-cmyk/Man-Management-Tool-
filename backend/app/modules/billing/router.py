from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.billing.schemas import (
    BillingConfigureRequest,
    BillingConfigureResponse,
    InvoiceRequest,
    InvoiceResponse,
    MarkReadyForBillingRequest,
    MarkReadyForBillingResponse,
    ProformaRequest,
    ProformaResponse,
    RemoveReadinessRequest,
    RemoveReadinessResponse,
)
from app.modules.billing.service import BillingService

router = APIRouter(prefix="/wm/billing", tags=["Work Management - Billing"])


@router.post("/configure", response_model=BillingConfigureResponse)
def configure_billing(payload: BillingConfigureRequest, db: Session = Depends(get_db)):
    return BillingService(db).configure_billing(payload)


@router.post("/mark-ready", response_model=MarkReadyForBillingResponse)
def mark_ready_for_billing(payload: MarkReadyForBillingRequest, db: Session = Depends(get_db)):
    return BillingService(db).mark_ready_for_billing(payload)


@router.post("/remove-ready", response_model=RemoveReadinessResponse)
def remove_readiness(payload: RemoveReadinessRequest, db: Session = Depends(get_db)):
    return BillingService(db).remove_readiness(payload)


@router.post("/proforma", response_model=ProformaResponse)
def create_or_link_proforma(payload: ProformaRequest, db: Session = Depends(get_db)):
    return BillingService(db).process_proforma(payload)


@router.post("/invoice", response_model=InvoiceResponse)
def create_or_link_invoice(payload: InvoiceRequest, db: Session = Depends(get_db)):
    return BillingService(db).process_invoice(payload)
