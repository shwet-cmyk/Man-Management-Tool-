from __future__ import annotations

from datetime import UTC, datetime


class UxAnalyticsDAL:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.screen_rows: list[dict] = [
            {
                "screen_id": "task_entry_main",
                "screen_name": "Task Entry",
                "module": "Task",
                "views": 1820,
                "avg_time_seconds": 104,
                "dead_clicks": 148,
                "rage_clicks": 29,
                "dropoff_percent": 19.8,
                "error_events": 44,
                "completion_rate": 80.2,
                "last_updated": now,
                "field_abandonment": [{"field": "dependency", "count": 53}, {"field": "due_date", "count": 41}],
                "validation_hotspots": [{"field": "assignee", "failures": 32}, {"field": "planned_hours", "failures": 26}],
                "action_summary": [{"action": "save", "success_rate": 79.1}, {"action": "start", "success_rate": 92.0}],
                "low_confidence": False,
            },
            {
                "screen_id": "timesheet_entry_main",
                "screen_name": "Timesheet Entry",
                "module": "Timesheet",
                "views": 2401,
                "avg_time_seconds": 87,
                "dead_clicks": 214,
                "rage_clicks": 47,
                "dropoff_percent": 23.4,
                "error_events": 61,
                "completion_rate": 74.9,
                "last_updated": now,
                "field_abandonment": [{"field": "job_id", "count": 74}, {"field": "hours", "count": 52}],
                "validation_hotspots": [{"field": "hours", "failures": 48}, {"field": "date", "failures": 17}],
                "action_summary": [{"action": "save", "success_rate": 74.9}, {"action": "submit", "success_rate": 81.4}],
                "low_confidence": False,
            },
            {
                "screen_id": "automation_rule_entry",
                "screen_name": "Automation Rule Entry",
                "module": "Automation",
                "views": 93,
                "avg_time_seconds": 211,
                "dead_clicks": 5,
                "rage_clicks": 3,
                "dropoff_percent": 45.0,
                "error_events": 8,
                "completion_rate": 52.0,
                "last_updated": now,
                "field_abandonment": [{"field": "condition_builder", "count": 16}],
                "validation_hotspots": [{"field": "action_parameters", "failures": 11}],
                "action_summary": [{"action": "test_rule", "success_rate": 66.0}, {"action": "enable", "success_rate": 57.0}],
                "low_confidence": True,
            },
        ]
        self.heatmaps = {
            "task_entry_main": {"screen_id": "task_entry_main", "generated": True, "heatmap_ref": "s3://mock/heatmap/task_entry_latest.png"},
            "timesheet_entry_main": {"screen_id": "timesheet_entry_main", "generated": True, "heatmap_ref": "s3://mock/heatmap/timesheet_entry_latest.png"},
            "automation_rule_entry": {"screen_id": "automation_rule_entry", "generated": False, "fallback": "Heatmap unavailable for selected period; showing aggregate click density."},
        }
        self.improvement_tickets: list[dict] = []
        self.compare_snapshots: list[dict] = []

    def list_screens(self) -> list[dict]:
        return list(self.screen_rows)

    def get_screen(self, screen_id: str) -> dict | None:
        return next((r for r in self.screen_rows if r["screen_id"] == screen_id), None)

    def get_heatmap(self, screen_id: str) -> dict | None:
        return self.heatmaps.get(screen_id)

    def save_ticket(self, ticket: dict) -> dict:
        self.improvement_tickets.append(ticket)
        return ticket

    def save_compare_snapshot(self, snapshot: dict) -> dict:
        self.compare_snapshots.append(snapshot)
        return snapshot
