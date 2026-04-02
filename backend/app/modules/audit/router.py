from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.audit.schemas import AuditLogCreateRequest
from app.modules.audit.service import AuditService

router = APIRouter(prefix="/audit", tags=["Work Management - Audit"])


@router.post("/log")
def log_audit(payload: AuditLogCreateRequest, db: Session = Depends(get_db)):
    return AuditService(db).log_event(payload)


@router.get("/{entity_type}/{entity_id}")
def get_audit_logs(entity_type: str, entity_id: int, db: Session = Depends(get_db)):
    return AuditService(db).get_audit_logs(entity_type, entity_id)


@router.get("/{audit_log_id}/changes")
def get_field_changes(audit_log_id: int, db: Session = Depends(get_db)):
    return AuditService(db).get_field_changes(audit_log_id)


@router.get("/version/{entity_type}/{entity_id}/{version_no}")
def get_version(entity_type: str, entity_id: int, version_no: int, db: Session = Depends(get_db)):
    return AuditService(db).get_version_snapshot(entity_type, entity_id, version_no)
