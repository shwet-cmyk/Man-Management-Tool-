from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.jobs.schemas import GovernanceConfigRequest, JobCreateRequest, JobStatusTransitionRequest, TaskShellCreateRequest, TransferDecisionRequest
from app.modules.jobs.service import JobGovernanceService

router = APIRouter(prefix="/wm/jobs", tags=["Jobs Governance"])


@router.post("/task-shell")
def create_task_shell(payload: TaskShellCreateRequest, db: Session = Depends(get_db)):
    return JobGovernanceService(db).create_task_shell(payload)


@router.post("")
def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    return JobGovernanceService(db).create_job(payload)


@router.post("/{job_id}/status")
def transition_job(job_id: int, payload: JobStatusTransitionRequest, db: Session = Depends(get_db)):
    return JobGovernanceService(db).transition_job_status(job_id, payload)


@router.post("/{job_id}/transfer-decision")
def transfer_decision(job_id: int, payload: TransferDecisionRequest, db: Session = Depends(get_db)):
    return JobGovernanceService(db).decide_transfer(job_id, payload)


@router.post("/governance-config")
def configure(payload: GovernanceConfigRequest, db: Session = Depends(get_db)):
    return JobGovernanceService(db).configure(payload)


@router.get("/dashboard-metrics")
def dashboard_metrics(db: Session = Depends(get_db)):
    return JobGovernanceService(db).dashboard_metrics()


@router.get("/reports/registers")
def report_registers(db: Session = Depends(get_db)):
    return JobGovernanceService(db).report_registers()
