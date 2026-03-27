from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.approval.schemas import ApprovalActionRequest, ApprovalSubmitRequest, ApprovalWorkflowCreateRequest
from app.modules.approval.service import ApprovalService

router = APIRouter(prefix="/approval", tags=["Work Management - Approval Engine"])


@router.post("/workflows")
def create_workflow(payload: ApprovalWorkflowCreateRequest, db: Session = Depends(get_db)):
    return ApprovalService(db).create_workflow(payload)


@router.post("/submit")
def submit_for_approval(payload: ApprovalSubmitRequest, db: Session = Depends(get_db)):
    return ApprovalService(db).submit(payload)


@router.post("/action")
def take_action(payload: ApprovalActionRequest, db: Session = Depends(get_db)):
    return ApprovalService(db).action(payload)


@router.get("/status/{entity_id}")
def get_status(entity_id: int, db: Session = Depends(get_db)):
    return ApprovalService(db).status_by_entity(entity_id)
