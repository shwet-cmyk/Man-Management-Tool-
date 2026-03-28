from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.wm_ticket import WmTicket
from app.modules.ticket_integration.audit_service import IntegrationAuditService
from app.modules.ticket_integration.mappers import TicketMapperService
from app.modules.ticket_integration.schemas import IntegrationConfigRequest, TicketFetchRequest
from app.modules.ticket_integration.ticket_api_service import TicketApiService


class TicketSyncService:
    def __init__(self, db: Session, config: IntegrationConfigRequest):
        self.db = db
        self.config = config
        self.mapper = TicketMapperService()
        self.audit = IntegrationAuditService(db)

    def run_sync(self, payload: TicketFetchRequest) -> dict:
        api = TicketApiService(force_mock=payload.use_mock if payload.use_mock is not None else self.config.mock_mode)
        sync_log = self.audit.start_sync_log(payload.mode, payload.triggered_by, self.config.source_system_name)

        if payload.mode == "incremental" and payload.updated_after is None:
            payload.updated_after = self._last_sync_timestamp()

        result = api.fetch_tickets(
            updated_after=payload.updated_after,
            from_date=payload.from_date,
            to_date=payload.to_date,
            status=payload.status,
            priority=payload.priority,
            ticket_no=payload.ticket_no,
            open_only=payload.open_only,
            limit=payload.limit,
        )

        if not result.get("success"):
            self.audit.complete_sync_log(sync_log, "FAILED", 0, 0, 0, 0, 1, error_summary=result.get("message"))
            self.db.commit()
            return {
                "status": result.get("error_type", "failure"),
                "sync_run_id": sync_log.id,
                "source": self.config.source_system_name,
                "message": result.get("message"),
                "summary": {
                    "fetched_count": 0,
                    "inserted_count": 0,
                    "updated_count": 0,
                    "skipped_count": 0,
                    "failed_count": 1,
                },
            }

        inserted = 0
        updated = 0
        skipped = 0
        failed = 0
        failures: list[str] = []

        for row in result.get("tickets", []):
            try:
                mapped = self.mapper.to_ticket_record(row, created_by=payload.triggered_by)
                existing = self.db.query(WmTicket).filter(
                    (WmTicket.ticket_no == mapped["ticket_no"]) | (WmTicket.external_ticket_no == mapped["external_ticket_no"])
                ).first()
                if existing:
                    for k, v in mapped.items():
                        setattr(existing, k, v)
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    new_ticket_id = int((self.db.query(WmTicket.ticket_id).order_by(WmTicket.ticket_id.desc()).first() or (0,))[0] or 0) + 1
                    self.db.add(WmTicket(ticket_id=new_ticket_id, **mapped))
                    inserted += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                failures.append(str(exc))

        fetched = len(result.get("tickets", []))
        skipped = max(fetched - inserted - updated - failed, 0)
        status = "PARTIAL_SUCCESS" if failed > 0 and (inserted + updated) > 0 else ("FAILED" if failed == fetched and fetched > 0 else "SUCCESS")
        self.audit.complete_sync_log(sync_log, status, fetched, inserted, updated, skipped, failed, error_summary="; ".join(failures[:5]) if failures else None)
        self.db.commit()

        return {
            "status": "partial_success" if status == "PARTIAL_SUCCESS" else ("failure" if status == "FAILED" else "success"),
            "sync_run_id": sync_log.id,
            "source": self.config.source_system_name,
            "last_sync_time": sync_log.completed_at,
            "summary": {
                "fetched_count": fetched,
                "inserted_count": inserted,
                "updated_count": updated,
                "skipped_count": skipped,
                "failed_count": failed,
            },
        }

    def _last_sync_timestamp(self):
        row = self.db.query(WmTicket).order_by(WmTicket.updated_on.desc(), WmTicket.created_on.desc()).first()
        return row.updated_on or row.created_on if row else None
