from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.crm.schemas import DealCreateRequest, DealInvoiceRequest, FollowupCreateRequest, LeadCreateRequest, LifecycleUpdateRequest
from app.modules.crm.service import CrmService

router = APIRouter(prefix="/crm", tags=["Work Management - CRM Pipeline"])


@router.post("/lead")
def create_lead(payload: LeadCreateRequest, performed_by: int = Query(0), db: Session = Depends(get_db)):
    return CrmService(db).create_lead(payload, performed_by)


@router.post("/lead/{lead_id}/convert")
def convert_lead(lead_id: int, performed_by: int = Query(0), db: Session = Depends(get_db)):
    return CrmService(db).convert_lead_to_opportunity(lead_id, performed_by)


@router.post("/deal")
def create_deal(payload: DealCreateRequest, performed_by: int = Query(0), db: Session = Depends(get_db)):
    return CrmService(db).create_deal(payload, performed_by)


@router.post("/deal/{deal_id}/invoice")
def deal_to_invoice(deal_id: int, payload: DealInvoiceRequest, db: Session = Depends(get_db)):
    return CrmService(db).convert_deal_to_invoice(deal_id, payload)


@router.post("/followup")
def create_followup(payload: FollowupCreateRequest, db: Session = Depends(get_db)):
    return CrmService(db).create_followup(payload)


@router.get("/followup/due")
def due_followups(db: Session = Depends(get_db)):
    return CrmService(db).due_followups()


@router.post("/customer/lifecycle")
def upsert_lifecycle(payload: LifecycleUpdateRequest, db: Session = Depends(get_db)):
    return CrmService(db).upsert_customer_lifecycle(payload)
