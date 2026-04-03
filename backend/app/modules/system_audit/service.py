from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException


class AuditService:
    def __init__(self) -> None:
        self.entries: dict[int, dict] = {}

    def add(self, payload: dict[str, Any]) -> dict:
        next_id = len(self.entries) + 1
        row = {"audit_id": next_id, **payload, "timestamp": datetime.utcnow()}
        self.entries[next_id] = row
        return row

    def list(
        self,
        *,
        user_name: str | None = None,
        action_type: str | None = None,
        module: str | None = None,
        reference_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict]:
        rows = list(self.entries.values())
        if user_name:
            rows = [r for r in rows if r["user_name"] == user_name]
        if action_type:
            rows = [r for r in rows if r["action_type"] == action_type]
        if module:
            rows = [r for r in rows if r["module"] == module]
        if reference_id:
            rows = [r for r in rows if str(r["reference_id"]) == str(reference_id)]
        if date_from:
            rows = [r for r in rows if r["timestamp"] >= date_from]
        if date_to:
            rows = [r for r in rows if r["timestamp"] <= date_to]
        return rows

    def detail(self, audit_id: int) -> dict:
        row = self.entries.get(audit_id)
        if not row:
            raise HTTPException(status_code=404, detail="Audit entry not found")
        return {
            "action_summary": {
                "user": row["user_name"],
                "action": row["action_type"],
                "module": row["module"],
                "record_id": row["reference_id"],
                "timestamp": row["timestamp"],
            },
            "field_level_change": {
                "field": row.get("field_name"),
                "old": row.get("old_value"),
                "new": row.get("new_value"),
            },
            "context": row.get("context"),
        }

    def search(self, q: str) -> list[dict]:
        return [
            r
            for r in self.entries.values()
            if q.lower() in str(r.get("user_name", "")).lower()
            or q.lower() in str(r.get("reference_id", "")).lower()
            or q.lower() in str(r.get("field_name") or "").lower()
            or q.lower() in str(r.get("old_value") or "").lower()
            or q.lower() in str(r.get("new_value") or "").lower()
        ]

    def reports(self) -> dict:
        rows = list(self.entries.values())
        return {
            "user_activity_report": rows,
            "change_log_report": [r for r in rows if r.get("field_name")],
            "critical_change_report": [r for r in rows if r.get("field_name") in {"status", "end_date", "due_date", "cost"}],
            "rollover_audit": [r for r in rows if r["action_type"] == "ROLLOVER"],
            "approval_audit": [r for r in rows if r["module"] == "APPROVAL"],
        }

    def analytics(self) -> dict:
        rows = list(self.entries.values())
        users = sorted({r["user_name"] for r in rows})
        fields = sorted({r["field_name"] for r in rows if r.get("field_name")})
        return {
            "most_active_users": sorted(
                [{"user": u, "events": len([r for r in rows if r["user_name"] == u])} for u in users],
                key=lambda x: x["events"],
                reverse=True,
            ),
            "most_edited_fields": sorted(
                [{"field": f, "edits": len([r for r in rows if r.get("field_name") == f])} for f in fields],
                key=lambda x: x["edits"],
                reverse=True,
            ),
            "frequent_delays": len([r for r in rows if r["action_type"] in {"JOB_DELAYED", "TASK_DELAY", "PROJECT_DELAY"}]),
            "system_misuse_patterns": len([r for r in rows if r["action_type"] == "ADMIN_OVERRIDE"]),
        }


audit_service = AuditService()
