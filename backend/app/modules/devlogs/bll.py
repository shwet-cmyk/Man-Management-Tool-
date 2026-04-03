from __future__ import annotations

from datetime import UTC, datetime

from app.modules.devlogs.dal import DevlogsDAL


class DevlogsBLL:
    def __init__(self, dal: DevlogsDAL) -> None:
        self.dal = dal

    def filter(self, payload: dict) -> list[dict]:
        rows = self.dal.list_all()
        if payload.get("module"):
            rows = [r for r in rows if r["module"].lower() == payload["module"].lower()]
        if payload.get("severity"):
            rows = [r for r in rows if r["severity"].lower() == payload["severity"].lower()]
        if payload.get("event_type"):
            rows = [r for r in rows if r["event_type"].lower() == payload["event_type"].lower()]
        if payload.get("status"):
            rows = [r for r in rows if r["status"].lower() == payload["status"].lower()]
        if payload.get("correlation_id"):
            rows = [r for r in rows if payload["correlation_id"].lower() in r["correlation_id"].lower()]
        if payload.get("release_version"):
            rows = [r for r in rows if r["release_version"] == payload["release_version"]]
        return rows

    def dashboard(self) -> dict:
        rows = self.dal.list_all()
        critical = [r for r in rows if r["severity"].lower() == "critical"]
        failures = [r for r in rows if r["event_type"].lower() == "error"]
        return {
            "kpis": {
                "total_errors": len(failures),
                "critical_errors": len(critical),
                "api_failure_rate": 0.037,
                "avg_api_response_time_ms": 842,
                "slowest_screen": "Timesheet Entry",
                "failed_background_jobs": 3,
                "integration_failures": 2,
                "post_release_spike_indicator": True,
            },
            "last_ingested_timestamp": datetime.now(UTC),
            "records": rows,
        }

    def add_note(self, row: dict, note: str, added_by: str) -> None:
        row["notes"].append({"note": note, "added_by": added_by, "at": datetime.now(UTC)})
