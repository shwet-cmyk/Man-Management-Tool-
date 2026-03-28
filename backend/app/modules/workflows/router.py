from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.workflows.schemas import (
    SlaControlRequest,
    TriggerWorkflowRequest,
    WorkflowApprovalDecisionRequest,
    WorkflowCreateRequest,
    WorkflowEdgeRequest,
    WorkflowNodeRequest,
    WorkflowUpdateRequest,
)
from app.modules.workflows.service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Work Management - Workflow Builder"])


class SlaRuleRequest(BaseModel):
    time_limit_minutes: int
    escalation_user_id: int


@router.post("")
def create_workflow(payload: WorkflowCreateRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).create_workflow(payload)


@router.post("/create")
def create_workflow_alias(payload: WorkflowCreateRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).create_workflow(payload)


@router.get("")
def list_workflows(db: Session = Depends(get_db)):
    return WorkflowService(db).list_workflows()


@router.put("/{workflow_id}")
def update_workflow(workflow_id: int, payload: WorkflowUpdateRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).update_workflow(workflow_id, payload)


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    return WorkflowService(db).delete_workflow(workflow_id)


@router.post("/{workflow_id}/nodes")
def add_node(workflow_id: int, payload: WorkflowNodeRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).add_node(workflow_id, payload)


@router.post("/{workflow_id}/edges")
def add_edge(workflow_id: int, payload: WorkflowEdgeRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).add_edge(workflow_id, payload)


@router.post("/{workflow_id}/sla")
def add_sla(workflow_id: int, payload: SlaRuleRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).add_sla_rule(workflow_id, payload.time_limit_minutes, payload.escalation_user_id)


@router.post("/trigger")
def trigger_workflow(payload: TriggerWorkflowRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).trigger_workflow(payload)


@router.post("/approval/approve")
def approve(payload: WorkflowApprovalDecisionRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).approve(payload)


@router.post("/approve")
def approve_alias(payload: WorkflowApprovalDecisionRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).approve(payload)


@router.post("/approval/reject")
def reject(payload: WorkflowApprovalDecisionRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).reject(payload)


@router.post("/sla/pause")
def pause_sla(payload: SlaControlRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).pause_sla(payload.instance_id)


@router.post("/sla/resume")
def resume_sla(payload: SlaControlRequest, db: Session = Depends(get_db)):
    return WorkflowService(db).resume_sla(payload.instance_id)


@router.post("/sla/process")
def process_sla(db: Session = Depends(get_db)):
    return WorkflowService(db).process_sla_breaches()


@router.get("/status/{instance_id}")
def get_workflow_status(instance_id: int, db: Session = Depends(get_db)):
    return WorkflowService(db).get_execution_status(instance_id)
