from __future__ import annotations

from datetime import datetime

REQUIRED_INTERCONNECTS = [
    ("PROJECT", "PHASE"),
    ("PHASE", "TASK"),
    ("TASK", "JOB"),
    ("JOB", "TIMESHEET"),
    ("TIMESHEET", "COSTING"),
    ("COSTING", "PROFITABILITY"),
    ("TASK", "SLA"),
    ("JOB", "SLA"),
    ("TASK", "APPROVAL"),
    ("JOB", "APPROVAL"),
    ("STATUS", "NOTIFICATION"),
    ("STATUS", "AUDIT"),
    ("ROLLOVER", "AUDIT"),
    ("ROLLOVER", "GAMIFICATION"),
    ("DEPENDENCY", "UNLOCK"),
    ("PROJECT_DELAY", "GAMIFICATION"),
    ("APPROVAL_REJECT", "COMEBACK"),
    ("APPROVAL_APPROVE", "NEXT_LEVEL"),
    ("AUTOMATION", "NOTIFICATION"),
    ("AUTOMATION", "AUDIT"),
    ("DASHBOARD", "RBAC_SCOPE"),
]

COVERAGE: dict[tuple[str, str], dict] = {
    key: {"covered": False, "updated_at": datetime.utcnow(), "source": "SYSTEM"} for key in REQUIRED_INTERCONNECTS
}


def mark_covered(source: str, target: str, source_ref: str = "SYSTEM"):
    key = (source.upper(), target.upper())
    if key in COVERAGE:
        COVERAGE[key] = {"covered": True, "updated_at": datetime.utcnow(), "source": source_ref}


def coverage_matrix() -> list[dict]:
    return [
        {
            "source": s,
            "target": t,
            "covered": meta["covered"],
            "updated_at": meta["updated_at"],
            "source_ref": meta["source"],
        }
        for (s, t), meta in COVERAGE.items()
    ]


def uncovered() -> list[dict]:
    return [row for row in coverage_matrix() if not row["covered"]]
