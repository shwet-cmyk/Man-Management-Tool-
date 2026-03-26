from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.tickets.schemas import TicketAssignRequest, TicketCommentRequest, TicketCreateRequest, TicketUpdateRequest
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


@router.get("/{ticket_id}/timeline")
def get_timeline(ticket_id: int, db: Session = Depends(get_db)):
    return TicketService(db).timeline(ticket_id)
