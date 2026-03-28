from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.tez_audit.schemas import TezAuditLogRequest
from app.modules.tez_audit.service import TezAuditService

router = APIRouter(prefix="/audit", tags=["TEZ Audit"])


@router.post("/log")
def log_audit(payload: TezAuditLogRequest, db: Session = Depends(get_db)):
    return TezAuditService(db).log_event(payload)


@router.get("/{entity_type}/{entity_id}")
def get_audit_logs(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    return TezAuditService(db).get_entity_logs(entity_type, entity_id)


@router.post("/{entity_type}/{entity_id}/soft-delete/{user_id}")
def soft_delete(entity_type: str, entity_id: str, user_id: str, db: Session = Depends(get_db)):
    return TezAuditService(db).soft_delete_with_audit(entity_type, entity_id, user_id)
