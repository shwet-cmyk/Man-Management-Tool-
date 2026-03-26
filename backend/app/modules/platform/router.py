from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.dashboard.schemas import DashboardCreateRequest, WidgetAddRequest
from app.modules.dashboard.service import DashboardService
from app.modules.sla.service import SlaService
from app.modules.workflows.schemas import TriggerWorkflowRequest, WorkflowCreateRequest
from app.modules.workflows.service import WorkflowService

router = APIRouter(prefix="", tags=["Platform Aliases"])


@router.post("/widget")
def create_widget_alias(payload: WidgetAddRequest, db: Session = Depends(get_db)):
    return DashboardService(db).add_widget(payload)


@router.post("/workflow")
def create_workflow_alias(payload: WorkflowCreateRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).create_workflow(payload)


@router.post("/workflow/execute")
def execute_workflow_alias(payload: TriggerWorkflowRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).trigger_workflow(payload)


@router.get("/sla/status")
def sla_status_alias(entity_type: str, entity_id: int, db: Session = Depends(get_db)):
    return SlaService(db).get_status(entity_type, entity_id)
