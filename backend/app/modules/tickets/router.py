from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.tickets.schemas import (
    EscalationDigestRequest,
    TaskRolloverRequest,
    TicketAssignRequest,
    TicketCommentRequest,
    TicketConvertToTaskRequest,
    TicketCreateRequest,
    TicketDashboardRequest,
    TicketFollowupRequest,
    TicketPauseRequest,
    TicketUpdateRequest,
)
from app.modules.tickets.service import TicketService

router = APIRouter(prefix="/wm/tickets", tags=["Work Management - Tickets"])


@router.post("")
def create_ticket(payload: TicketCreateRequest, db: Session = Depends(get_db)):
    return TicketService(db).create_ticket(payload)


@router.put("/{ticket_id}")
def update_ticket(ticket_id: int, payload: TicketUpdateRequest, db: Session = Depends(get_db)):
    return TicketService(db).update_ticket(ticket_id, payload)


@router.post("/{ticket_id}/comments")
def add_comment(ticket_id: int, payload: TicketCommentRequest, db: Session = Depends(get_db)):
    return TicketService(db).add_comment(ticket_id, payload)


@router.post("/{ticket_id}/assign")
def assign_users(ticket_id: int, payload: TicketAssignRequest, db: Session = Depends(get_db)):
    return TicketService(db).assign_users(ticket_id, payload)


@router.post("/{ticket_id}/followups")
def add_followup(ticket_id: int, payload: TicketFollowupRequest, db: Session = Depends(get_db)):
    return TicketService(db).add_followup(ticket_id, payload)


@router.post("/{ticket_id}/pause")
def pause_or_resume(ticket_id: int, payload: TicketPauseRequest, db: Session = Depends(get_db)):
    return TicketService(db).pause_or_resume(ticket_id, payload)


@router.post("/{ticket_id}/convert-to-task")
def convert_to_task(ticket_id: int, payload: TicketConvertToTaskRequest, db: Session = Depends(get_db)):
    return TicketService(db).convert_to_task(ticket_id, payload)


@router.post("/rollovers")
def register_rollover(payload: TaskRolloverRequest, db: Session = Depends(get_db)):
    return TicketService(db).register_task_rollover(payload)


@router.post("/dashboard")
def dashboard_metrics(payload: TicketDashboardRequest, db: Session = Depends(get_db)):
    return TicketService(db).dashboard_metrics(payload)


@router.post("/escalation/daily-digest")
def daily_digest(payload: EscalationDigestRequest, db: Session = Depends(get_db)):
    return TicketService(db).daily_escalation_digest(payload)


@router.get("/{ticket_id}/timeline")
def get_timeline(ticket_id: int, db: Session = Depends(get_db)):
    return TicketService(db).timeline(ticket_id)
