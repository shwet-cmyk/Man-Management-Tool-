from __future__ import annotations

from datetime import UTC, datetime


class DevlogsDAL:
    def __init__(self) -> None:
        self.rows: list[dict] = [
            {
                "id": 1,
                "timestamp": datetime.now(UTC),
                "event_type": "Error",
                "module": "Tasks",
                "surface": "POST /api/tasks/create",
                "severity": "Critical",
                "user_context": "tenant:alpha role:manager",
                "correlation_id": "corr-71aa-task",
                "status": "Open",
                "release_version": "v3.5.1",
                "message": "Validation handler returned 500 on dependency cycle edge case",
                "stack_trace": "Traceback...",
                "request_payload": {"task_name": "Q2 Close", "dependency_id": 342},
                "response_payload": {"detail": "Unhandled ValueError"},
                "masked": False,
                "notes": [],
                "ticket_ref": None,
            },
            {
                "id": 2,
                "timestamp": datetime.now(UTC),
                "event_type": "Performance",
                "module": "Timesheet",
                "surface": "Timesheet Entry Screen",
                "severity": "High",
                "user_context": "tenant:beta role:user",
                "correlation_id": "corr-11ac-time",
                "status": "Investigating",
                "release_version": "v3.5.1",
                "message": "Median API latency rose to 1.8s after release",
                "stack_trace": None,
                "request_payload": {"masked": True},
                "response_payload": {"masked": True},
                "masked": True,
                "notes": [{"note": "Investigate db index on timesheet_date", "added_by": "devops.lead", "at": datetime.now(UTC)}],
                "ticket_ref": "TKT-9021",
            },
        ]

    def list_all(self) -> list[dict]:
        return list(self.rows)

    def get(self, item_id: int) -> dict | None:
        return next((r for r in self.rows if r["id"] == item_id), None)
