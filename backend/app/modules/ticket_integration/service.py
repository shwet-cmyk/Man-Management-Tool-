from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog
from app.models.wm_task import WmTask
from app.models.wm_ticket import WmTicket
from app.modules.ticket_integration.schemas import IntegrationConfigRequest, TaskFromTicketRequest, TicketFetchRequest
from app.modules.ticket_integration.sync_service import TicketSyncService
from app.modules.ticket_integration.task_creation_service import TicketTaskCreationService


class TicketIntegrationService:
    _config = IntegrationConfigRequest()

    def __init__(self, db: Session):
        self.db = db

    @classmethod
    def set_config(cls, cfg: IntegrationConfigRequest) -> IntegrationConfigRequest:
        cls._config = cfg
        return cls._config

    @classmethod
    def get_config(cls) -> IntegrationConfigRequest:
        return cls._config

    def sync_tickets(self, payload: TicketFetchRequest) -> dict:
        return TicketSyncService(self.db, self._config).run_sync(payload)

    def create_task_from_ticket(self, payload: TaskFromTicketRequest) -> dict:
        return TicketTaskCreationService(self.db, self._config).create_from_ticket(payload)

    def integration_dashboard(self) -> dict:
        last_sync = self.db.query(SyncLog).filter(SyncLog.entity.like("ticket_integration:%")).order_by(SyncLog.id.desc()).first()
        total_tickets = self.db.query(WmTicket).count()
        converted_ticket_ids = {x[0] for x in self.db.query(WmTask.source_ticket_id).filter(WmTask.source_ticket_id.isnot(None)).all()}
        available = self.db.query(WmTicket).filter(~WmTicket.ticket_id.in_(converted_ticket_ids) if converted_ticket_ids else True).count()
        converted = len(converted_ticket_ids)

        return {
            "latest_synced_tickets": total_tickets,
            "last_sync_time": last_sync.completed_at if last_sync else None,
            "sync_summary": {
                "status": last_sync.status if last_sync else "N/A",
                "fetched_count": last_sync.total_fetched if last_sync else 0,
                "inserted_count": last_sync.inserted if last_sync else 0,
                "updated_count": last_sync.updated if last_sync else 0,
                "skipped_count": last_sync.skipped if last_sync else 0,
                "failed_count": last_sync.failed if last_sync else 0,
            },
            "tickets_available_for_task_creation": available,
            "tickets_already_converted_to_tasks": converted,
            "task_creation_success_count": converted,
            "task_creation_failure_count": self.db.query(SyncLog).filter(SyncLog.entity.like("ticket_integration:%"), SyncLog.status == "FAILED").count(),
        }
