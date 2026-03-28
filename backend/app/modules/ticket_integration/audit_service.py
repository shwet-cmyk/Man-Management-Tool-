from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog
from app.models.task_audit_log import TaskAuditLog


class IntegrationAuditService:
    def __init__(self, db: Session):
        self.db = db

    def start_sync_log(self, sync_type: str, triggered_by: int, source_name: str) -> SyncLog:
        row = SyncLog(
            entity=f"ticket_integration:{source_name}:by:{triggered_by}",
            sync_mode=sync_type,
            status="RUNNING",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def complete_sync_log(self, row: SyncLog, status: str, fetched: int, inserted: int, updated: int, skipped: int, failed: int, error_summary: str | None = None) -> None:
        row.status = status
        row.total_fetched = fetched
        row.inserted = inserted
        row.updated = updated
        row.skipped = skipped
        row.failed = failed
        row.error_details = error_summary
        row.completed_at = datetime.utcnow()

    def task_creation_log(self, *, ticket_no: str, task_no: str | None, created_by: int, mapping_status: str, duplicate_check_status: str, source_system: str, message: str) -> None:
        details = (
            f"ticket_no={ticket_no};task_no={task_no};mapping_status={mapping_status};"
            f"duplicate_check_status={duplicate_check_status};source_system={source_system};message={message}"
        )
        self.db.add(TaskAuditLog(entity_name="ticket_task_integration", entity_id=0, action="TASK_FROM_TICKET", details=details, created_by=created_by))
