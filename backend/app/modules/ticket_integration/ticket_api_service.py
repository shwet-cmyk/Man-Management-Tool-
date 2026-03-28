from __future__ import annotations

from datetime import datetime

from app.core.config import settings
from app.integrations.api_client import ApiClient, ApiError
from app.modules.ticket_integration.mock_data import build_mock_tickets


class TicketApiService:
    def __init__(self, force_mock: bool | None = None):
        self.mock_mode = settings.ticket_api_mock_mode if force_mock is None else force_mock
        self.client = ApiClient(
            base_url=settings.ticket_api_base_url,
            timeout_seconds=settings.ticket_api_timeout_seconds,
            max_retries=settings.ticket_api_max_retries,
            auth_mode=settings.ticket_api_auth_mode,
            token=settings.ticket_api_key,
            api_key_header=settings.ticket_api_key_header,
            extra_headers={"Accept": "application/json"},
        )

    def fetch_tickets(self, *, updated_after: datetime | None = None, from_date: datetime | None = None, to_date: datetime | None = None, status: str | None = None, priority: str | None = None, ticket_no: str | None = None, open_only: bool = False, limit: int = 100) -> dict:
        if self.mock_mode:
            rows = self._filter_mock(build_mock_tickets(), updated_after=updated_after, status=status, priority=priority, ticket_no=ticket_no, open_only=open_only, limit=limit)
            return {"success": True, "mode": "mock", "tickets": rows}

        params = {
            "updated_after": updated_after.isoformat() if updated_after else None,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "status": "OPEN" if open_only else status,
            "priority": priority,
            "ticket_no": ticket_no,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}

        try:
            result = self.client.get(settings.ticket_api_ticket_endpoint, params=params)
            data = result.get("data", [])
            tickets = data if isinstance(data, list) else [data]
            return {"success": True, "mode": "real", "tickets": tickets}
        except ApiError as exc:
            return {
                "success": False,
                "mode": "real",
                "error_type": exc.category,
                "message": exc.message,
                "retryable": exc.retryable,
                "tickets": [],
            }

    def _filter_mock(self, rows: list[dict], *, updated_after: datetime | None, status: str | None, priority: str | None, ticket_no: str | None, open_only: bool, limit: int) -> list[dict]:
        out = rows
        if ticket_no:
            out = [r for r in out if str(r.get("ticket_no")) == str(ticket_no)]
        if open_only:
            out = [r for r in out if str(r.get("status", "")).upper() == "OPEN"]
        elif status:
            out = [r for r in out if str(r.get("status", "")).upper() == str(status).upper()]
        if priority:
            out = [r for r in out if str(r.get("priority", "")).upper() == str(priority).upper()]
        if updated_after:
            out = [r for r in out if str(r.get("created_on", "")) >= updated_after.isoformat()]
        return out[:limit]
