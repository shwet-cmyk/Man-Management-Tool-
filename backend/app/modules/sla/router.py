from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.sla.schemas import HolidayCreateRequest, SlaControlRequest, SlaEscalateRequest, SlaRuleCreateRequest, SlaStartRequest
from app.modules.sla.service import SlaService

router = APIRouter(prefix="/wm/sla", tags=["Work Management - SLA + Escalation"])


@router.post("/rule")
def create_rule(payload: SlaRuleCreateRequest, db: Session = Depends(get_db)):
    return SlaService(db).create_rule(payload)


@router.post("/holiday")
def add_holiday(payload: HolidayCreateRequest, db: Session = Depends(get_db)):
    return SlaService(db).add_holiday(payload)


@router.post("/start")
def start_sla(payload: SlaStartRequest, db: Session = Depends(get_db)):
    return SlaService(db).start_sla(payload)


@router.get("/status/{entity_type}/{entity_id}")
def get_status(entity_type: str, entity_id: int, db: Session = Depends(get_db)):
    return SlaService(db).get_status(entity_type, entity_id)


@router.post("/pause")
def pause(payload: SlaControlRequest, db: Session = Depends(get_db)):
    return SlaService(db).pause(payload.sla_instance_id)


@router.post("/resume")
def resume(payload: SlaControlRequest, db: Session = Depends(get_db)):
    return SlaService(db).resume(payload.sla_instance_id)


@router.post("/check")
def check_breaches(db: Session = Depends(get_db)):
    return SlaService(db).check_and_escalate()


@router.post("/escalate")
def escalate(payload: SlaEscalateRequest, db: Session = Depends(get_db)):
    return SlaService(db).escalate(payload)
