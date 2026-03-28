from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.ticket_integration.schemas import IntegrationConfigRequest, TaskFromTicketRequest, TicketFetchRequest
from app.modules.ticket_integration.service import TicketIntegrationService

router = APIRouter(prefix="/wm/ticket-integration", tags=["Ticket Integration"])


@router.post("/config")
def configure(payload: IntegrationConfigRequest):
    cfg = TicketIntegrationService.set_config(payload)
    return {"status": "success", "config": cfg.model_dump()}


@router.post("/sync")
def sync_tickets(payload: TicketFetchRequest, db: Session = Depends(get_db)):
    return TicketIntegrationService(db).sync_tickets(payload)


@router.post("/tasks/from-ticket")
def create_task_from_ticket(payload: TaskFromTicketRequest, db: Session = Depends(get_db)):
    return TicketIntegrationService(db).create_task_from_ticket(payload)


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return TicketIntegrationService(db).integration_dashboard()
