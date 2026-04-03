from __future__ import annotations

from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.tasks.router import workload_summary

router = APIRouter(prefix="/gamification", tags=["Gamification + Appraisal Engine"])


class SourceType(str, Enum):
    job = "JOB"
    ticket = "TICKET"
    task = "TASK"
    project = "PROJECT"
    dependency = "DEPENDENCY"


class EventType(str, Enum):
    job_completed_on_time = "JOB_COMPLETED_ON_TIME"
    job_delayed = "JOB_DELAYED"
    dependency_caused_delay = "DEPENDENCY_CAUSED_DELAY"
    dependency_received_delay = "DEPENDENCY_RECEIVED_DELAY"
    task_delay_causer = "TASK_DELAY_CAUSER"
    task_delay_team_impact = "TASK_DELAY_TEAM_IMPACT"
    project_delay = "PROJECT_DELAY"


POINT_RULES = {
    EventType.job_completed_on_time: 20,
    EventType.job_delayed: -20,
    EventType.dependency_caused_delay: -20,
    EventType.dependency_received_delay: -10,
    EventType.task_delay_causer: -20,
    EventType.task_delay_team_impact: -10,
    EventType.project_delay: -100,
}


class PointEventRequest(BaseModel):
    employee: str
    event_type: EventType
    source_type: SourceType
    source_id: int
    reason: str
    metadata: dict = Field(default_factory=dict)


POINT_EVENTS: list[dict] = []
MANUAL_OVERRIDE_LOG: list[dict] = []


def add_points_event(payload: PointEventRequest) -> dict:
    points = POINT_RULES[payload.event_type]
    row = {
        "event_id": len(POINT_EVENTS) + 1,
        **payload.model_dump(),
        "points": points,
        "at": datetime.utcnow(),
    }
    POINT_EVENTS.append(row)
    return row


def _delay_counts(employee: str):
    events = [e for e in POINT_EVENTS if e["employee"] == employee]
    return {
        "tasks_delayed": len([e for e in events if e["event_type"] in {EventType.task_delay_causer, EventType.task_delay_team_impact}]),
        "jobs_delayed": len([e for e in events if e["event_type"] == EventType.job_delayed]),
        "projects_delayed": len([e for e in events if e["event_type"] == EventType.project_delay]),
    }


def _appraisal(employee: str):
    events = [e for e in POINT_EVENTS if e["employee"] == employee]
    total_points = sum(e["points"] for e in events)
    score_pct = max(0.0, min(100.0, 50 + total_points / 4))

    if score_pct >= 80:
        calculated = 12.0
    elif score_pct >= 60:
        calculated = 9.0
    elif score_pct >= 40:
        calculated = 6.0
    else:
        calculated = 5.0

    delays = _delay_counts(employee)
    cap = 5.0 if delays["tasks_delayed"] > 5 or delays["jobs_delayed"] > 10 or delays["projects_delayed"] > 2 else 12.0
    final = min(calculated, cap)

    return {
        "total_points": total_points,
        "score_pct": round(score_pct, 2),
        "calculated_appraisal_pct": calculated,
        "rule_cap_pct": cap,
        "final_appraisal_pct": final,
        "capped": final < calculated,
        "delay_counts": delays,
    }


@router.post("/events")
def create_points_event(payload: PointEventRequest):
    return add_points_event(payload)


@router.get("/employee/{employee}")
def employee_widget(employee: str):
    appraisal = _appraisal(employee)
    events = [e for e in POINT_EVENTS if e["employee"] == employee]
    utilization = next((w for w in workload_summary() if w["employee"] == employee), None)

    breakdown = [
        {
            "points": e["points"],
            "event_type": e["event_type"],
            "reason": e["reason"],
            "source": {"type": e["source_type"], "id": e["source_id"]},
            "at": e["at"],
        }
        for e in events
    ]

    return {
        "employee": employee,
        "score": appraisal["total_points"],
        "utilization": utilization,
        "performance_snapshot": {
            "events": len(events),
            "delays": appraisal["delay_counts"],
        },
        "appraisal_indicator": {
            "expected_pct": appraisal["final_appraisal_pct"],
            "warning": "Appraisal capped at 5% due to delay thresholds" if appraisal["capped"] else None,
        },
        "points_breakdown": breakdown,
    }


@router.get("/admin/scoreboard")
def admin_scoreboard():
    employees = sorted({e["employee"] for e in POINT_EVENTS})
    rows = []
    for employee in employees:
        appraisal = _appraisal(employee)
        utilization = next((w for w in workload_summary() if w["employee"] == employee), None)
        rows.append(
            {
                "employee": employee,
                "points": appraisal["total_points"],
                "utilization": utilization["status"] if utilization else None,
                "delays": appraisal["delay_counts"],
                "appraisal_pct": appraisal["final_appraisal_pct"],
            }
        )
    return rows


@router.get("/reports/summary")
def gamification_reports():
    return {
        "daily_points_report": POINT_EVENTS,
        "weekly_performance": admin_scoreboard(),
        "monthly_scorecard": admin_scoreboard(),
        "quarterly_appraisal_report": admin_scoreboard(),
        "yearly_appraisal_summary": admin_scoreboard(),
    }


@router.get("/analytics/summary")
def gamification_analytics():
    board = admin_scoreboard()
    return {
        "top_performers": sorted(board, key=lambda x: x["points"], reverse=True)[:10],
        "chronic_delayers": sorted(board, key=lambda x: x["delays"]["jobs_delayed"], reverse=True)[:10],
        "dependency_failure_hotspots": [
            e for e in POINT_EVENTS if e["event_type"] in {EventType.dependency_caused_delay, EventType.dependency_received_delay}
        ],
        "team_wise_performance": board,
    }


@router.post("/admin/manual-override")
def admin_manual_override(employee: str, points: int, reason: str, admin_user: str):
    # Allowed only through explicit logged endpoint.
    row = {
        "override_id": len(MANUAL_OVERRIDE_LOG) + 1,
        "employee": employee,
        "points": points,
        "reason": reason,
        "admin_user": admin_user,
        "at": datetime.utcnow(),
    }
    MANUAL_OVERRIDE_LOG.append(row)
    POINT_EVENTS.append(
        {
            "event_id": len(POINT_EVENTS) + 1,
            "employee": employee,
            "event_type": "ADMIN_OVERRIDE",
            "source_type": "ADMIN",
            "source_id": row["override_id"],
            "reason": reason,
            "metadata": {"admin_user": admin_user},
            "points": points,
            "at": datetime.utcnow(),
        }
    )
    return row


@router.get("/audit-log")
def gamification_audit():
    return {"point_events": POINT_EVENTS, "manual_overrides": MANUAL_OVERRIDE_LOG}
