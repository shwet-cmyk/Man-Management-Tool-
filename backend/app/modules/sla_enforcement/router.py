from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.sla_enforcement.schemas import SlaPauseRequest, SlaStartRequestV2
from app.modules.sla_enforcement.service import SlaEnforcementService

router = APIRouter(prefix="/sla/enforcement", tags=["SLA Enforcement V2"])


@router.post("/start")
def start(payload: SlaStartRequestV2, db: Session = Depends(get_db)):
    return SlaEnforcementService(db).start_tracking(
        ticket_id=payload.ticket_id,
        priority=payload.priority,
        created_at=payload.created_at,
        timezone=payload.timezone,
    )


@router.get("/{sla_id}")
def get_status(sla_id: str, db: Session = Depends(get_db)):
    return SlaEnforcementService(db).get_status(sla_id)


@router.post("/monitor")
def monitor(db: Session = Depends(get_db)):
    return SlaEnforcementService(db).monitor_and_escalate()


@router.post("/pause-resume")
def pause_resume(payload: SlaPauseRequest, db: Session = Depends(get_db)):
    return SlaEnforcementService(db).pause_resume(payload.sla_id, payload.paused, payload.reason)
