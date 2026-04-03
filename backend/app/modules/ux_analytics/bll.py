from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean

from app.modules.ux_analytics.dal import UxAnalyticsDAL


class UxAnalyticsBLL:
    def __init__(self, dal: UxAnalyticsDAL) -> None:
        self.dal = dal

    @staticmethod
    def friction_index(row: dict) -> float:
        return round((row["dead_clicks"] * 0.25) + (row["rage_clicks"] * 0.6) + row["dropoff_percent"] + (row["error_events"] * 0.4), 2)

    def summary(self) -> dict:
        rows = self.dal.list_screens()
        most_frustrating = max(rows, key=self.friction_index)
        return {
            "kpis": {
                "total_sessions": 4314,
                "screen_views": sum(r["views"] for r in rows),
                "dead_clicks": sum(r["dead_clicks"] for r in rows),
                "rage_clicks": sum(r["rage_clicks"] for r in rows),
                "error_rate": round(sum(r["error_events"] for r in rows) / max(sum(r["views"] for r in rows), 1), 4),
                "dropoff_rate": round(mean([r["dropoff_percent"] for r in rows]), 2),
                "avg_time_on_screen_seconds": round(mean([r["avg_time_seconds"] for r in rows]), 2),
                "most_frustrating_screen": most_frustrating["screen_name"],
            },
            "screens": [{**r, "friction_index": self.friction_index(r)} for r in rows],
        }

    def filter(self, module: str | None, screen: str | None, error_present: bool | None, high_friction_only: bool) -> list[dict]:
        rows = self.dal.list_screens()
        if module:
            rows = [r for r in rows if r["module"].lower() == module.lower()]
        if screen:
            rows = [r for r in rows if r["screen_id"] == screen or r["screen_name"].lower() == screen.lower()]
        if error_present is not None:
            rows = [r for r in rows if (r["error_events"] > 0) == error_present]
        if high_friction_only:
            rows = [r for r in rows if self.friction_index(r) >= 60]
        return [{**r, "friction_index": self.friction_index(r)} for r in rows]

    def screen_detail(self, screen_id: str) -> dict | None:
        row = self.dal.get_screen(screen_id)
        if not row:
            return None
        return {
            "screen_summary": {**row, "friction_index": self.friction_index(row)},
            "user_journey_timeline": [
                {"step": "open", "percent": 100},
                {"step": "field_interaction", "percent": 92},
                {"step": "validation_pass", "percent": 83},
                {"step": "save_submit", "percent": row["completion_rate"]},
            ],
            "ai_recommendations": [
                "Rename ambiguous buttons and add inline examples on high-failure fields.",
                "Move frequently missed fields higher in the form layout.",
            ],
        }

    def compare(self, screen_ids: list[str]) -> dict:
        rows = [r for r in self.dal.list_screens() if r["screen_id"] in screen_ids]
        snapshot = {
            "snapshot_id": len(self.dal.compare_snapshots) + 1,
            "screen_ids": screen_ids,
            "created_at": datetime.now(UTC),
            "comparison": [{"screen_id": r["screen_id"], "completion_rate": r["completion_rate"], "dropoff_percent": r["dropoff_percent"], "friction_index": self.friction_index(r)} for r in rows],
        }
        return self.dal.save_compare_snapshot(snapshot)

    def create_ticket(self, screen_id: str, issue_summary: str, details: str | None, priority: str, requested_by: str) -> dict:
        ticket = {
            "ticket_id": f"UX-{len(self.dal.improvement_tickets) + 1:04d}",
            "screen_id": screen_id,
            "issue_summary": issue_summary,
            "details": details,
            "priority": priority,
            "requested_by": requested_by,
            "created_at": datetime.now(UTC),
        }
        return self.dal.save_ticket(ticket)
