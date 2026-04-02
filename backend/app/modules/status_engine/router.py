from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/status-engine", tags=["Status Engine"])


class ModuleType(str, Enum):
    project = "PROJECT"
    phase = "PHASE"
    task = "TASK"
    job = "JOB"
    ticket = "TICKET"


class WorkItemType(str, Enum):
    task = "TASK"
    job = "JOB"


class PriorityType(str, Enum):
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"


class StatusDefinitionRequest(BaseModel):
    status_name: str = Field(..., min_length=2)
    module: ModuleType
    description: str | None = None
    is_initial: bool = False
    is_final: bool = False
    is_pause_status: bool = False
    is_blocking_status: bool = False
    trigger_sla: bool = False
    pause_sla: bool = False
    resume_sla: bool = False
    color_code: str | None = None
    display_order: int = 0
    allowed_into_roles: list[str] = Field(default_factory=list)
    allowed_out_roles: list[str] = Field(default_factory=list)
    active: bool = True


class TransitionRuleRequest(BaseModel):
    module: ModuleType
    from_status: str
    to_status: str
    allowed: bool = True
    role: str
    approval_required: bool = False
    trigger_sla: bool = False
    trigger_interconnect: bool = False


class DependencyRequest(BaseModel):
    dependency_type: WorkItemType
    dependency_id: int


class WorkItemRequest(BaseModel):
    project_id: int
    item_name: str
    owner: str
    priority: PriorityType
    showstopper: bool = False
    start_date: datetime
    end_date: datetime
    dependency_flag: bool = False
    dependency: DependencyRequest | None = None


class StatusChangeRequest(BaseModel):
    status: str
    actor: str
    actor_role: str
    remark: str | None = None
    approval_granted: bool = False


STATUS_MASTER: dict[int, dict] = {}
TRANSITION_MATRIX: dict[int, dict] = {}
WORK_ITEMS: dict[WorkItemType, dict[int, dict]] = {
    WorkItemType.task: {},
    WorkItemType.job: {},
}
AUDIT_LOG: list[dict] = []
INTERCONNECT_EVENTS: list[dict] = []
NOTIFICATION_EVENTS: list[dict] = []


SLA_DAYS = {
    PriorityType.high: 3,
    PriorityType.medium: 3,
    PriorityType.low: 7,
}


def _log_audit(event: str, payload: dict):
    AUDIT_LOG.append({"event": event, "at": datetime.utcnow(), **payload})


def _status_for_module(module: ModuleType) -> list[dict]:
    return sorted(
        [row for row in STATUS_MASTER.values() if row["module"] == module and row["active"]],
        key=lambda row: row["display_order"],
    )


def _resolve_status(module: ModuleType, status_name: str) -> dict:
    for row in STATUS_MASTER.values():
        if row["module"] == module and row["status_name"] == status_name and row["active"]:
            return row
    raise HTTPException(status_code=422, detail=f"Unknown status '{status_name}' for module {module}")


def _initial_status(module: ModuleType) -> dict:
    options = [row for row in _status_for_module(module) if row["is_initial"]]
    if not options:
        raise HTTPException(status_code=422, detail=f"No initial status configured for {module}")
    return options[0]


def _resolve_transition(module: ModuleType, from_status: str, to_status: str) -> dict:
    for row in TRANSITION_MATRIX.values():
        if row["module"] == module and row["from_status"] == from_status and row["to_status"] == to_status:
            return row
    raise HTTPException(status_code=422, detail="Transition is not defined in central transition matrix")


def validate_status_transition(
    module: ModuleType,
    from_status: str,
    to_status: str,
    actor_role: str,
    approval_granted: bool = False,
) -> dict:
    current_status_def = _resolve_status(module, from_status)
    if current_status_def["is_final"]:
        raise HTTPException(status_code=422, detail="Final status cannot have outgoing transitions")

    transition = _resolve_transition(module, from_status, to_status)
    if not transition["allowed"]:
        raise HTTPException(status_code=422, detail="Transition denied")
    if transition["role"] != actor_role and actor_role != "Admin":
        raise HTTPException(status_code=403, detail="RBAC denied for transition")
    if transition["approval_required"] and not approval_granted:
        raise HTTPException(status_code=422, detail="Transition requires approval")

    next_status_def = _resolve_status(module, to_status)
    return {"transition": transition, "next_status_def": next_status_def}


def _compute_sla_due(priority: PriorityType, showstopper: bool, from_dt: datetime) -> datetime:
    days = 1 if showstopper else SLA_DAYS[priority]
    return from_dt + timedelta(days=days)


def _emit_notification(event: str, item: dict, message: str):
    NOTIFICATION_EVENTS.append(
        {
            "event": event,
            "work_item_type": item["item_type"],
            "work_item_id": item["item_id"],
            "owner": item["owner"],
            "message": message,
            "at": datetime.utcnow(),
        }
    )


def _emit_interconnect(event: str, item: dict, extra: dict | None = None):
    INTERCONNECT_EVENTS.append(
        {
            "event": event,
            "work_item_type": item["item_type"],
            "work_item_id": item["item_id"],
            "project_id": item["project_id"],
            "at": datetime.utcnow(),
            **(extra or {}),
        }
    )


def _dependency_ready(item_type: WorkItemType, item_id: int) -> bool:
    item = WORK_ITEMS[item_type].get(item_id)
    return bool(item and item["status"] == "COMPLETED")


def _project_rollup(project_id: int) -> dict:
    project_items = [
        row for table in WORK_ITEMS.values() for row in table.values() if row["project_id"] == project_id
    ]
    if not project_items:
        return {"project_id": project_id, "overall_status": "NO_WORK_ITEMS", "sla_breach": False}

    any_breach = any(row["sla_state"] == "BREACHED" for row in project_items)
    if all(row["status"] == "COMPLETED" for row in project_items):
        overall = "COMPLETED"
    elif any(row["status"] == "IN_PROGRESS" for row in project_items):
        overall = "IN_PROGRESS"
    elif any(row["status"] == "BLOCKED" for row in project_items):
        overall = "BLOCKED"
    else:
        overall = "OPEN"

    return {"project_id": project_id, "overall_status": overall, "sla_breach": any_breach}


def _default_seed():
    if STATUS_MASTER:
        return

    defaults = [
        ("DRAFT", ModuleType.task, True, False, False, False),
        ("ASSIGNED", ModuleType.task, False, False, False, False),
        ("IN_PROGRESS", ModuleType.task, False, False, False, False),
        ("PAUSED", ModuleType.task, False, False, True, True),
        ("COMPLETED", ModuleType.task, False, True, False, False),
        ("DRAFT", ModuleType.job, True, False, False, False),
        ("ASSIGNED", ModuleType.job, False, False, False, False),
        ("IN_PROGRESS", ModuleType.job, False, False, False, False),
        ("PAUSED", ModuleType.job, False, False, True, True),
        ("COMPLETED", ModuleType.job, False, True, False, False),
        ("OPEN", ModuleType.ticket, True, False, False, False),
        ("CUSTOMER_INPUT", ModuleType.ticket, False, False, True, True),
        ("DEVELOPMENT", ModuleType.ticket, False, False, False, False),
        ("DESIGN_TEAM", ModuleType.ticket, False, False, False, False),
        ("FUTURE", ModuleType.ticket, False, False, False, False),
        ("SUGGESTION", ModuleType.ticket, False, False, False, False),
        ("PUBLISHED", ModuleType.ticket, False, False, False, False),
        ("CLOSED", ModuleType.ticket, False, True, False, False),
    ]

    for idx, (name, module, initial, final, pause, blocking) in enumerate(defaults, start=1):
        STATUS_MASTER[idx] = {
            "status_id": idx,
            "status_name": name,
            "module": module,
            "description": f"Default status {name} for {module}",
            "is_initial": initial,
            "is_final": final,
            "is_pause_status": pause,
            "is_blocking_status": blocking,
            "trigger_sla": name in {"DRAFT", "ASSIGNED", "OPEN", "DEVELOPMENT"},
            "pause_sla": pause,
            "resume_sla": name in {"IN_PROGRESS", "DEVELOPMENT"},
            "color_code": None,
            "display_order": idx,
            "allowed_into_roles": ["Admin", "Project Manager", "Assigned User"],
            "allowed_out_roles": ["Admin", "Project Manager", "Assigned User"],
            "active": True,
        }

    transitions = [
        (ModuleType.task, "DRAFT", "ASSIGNED"),
        (ModuleType.task, "ASSIGNED", "IN_PROGRESS"),
        (ModuleType.task, "IN_PROGRESS", "PAUSED"),
        (ModuleType.task, "PAUSED", "IN_PROGRESS"),
        (ModuleType.task, "IN_PROGRESS", "COMPLETED"),
        (ModuleType.job, "DRAFT", "ASSIGNED"),
        (ModuleType.job, "ASSIGNED", "IN_PROGRESS"),
        (ModuleType.job, "IN_PROGRESS", "PAUSED"),
        (ModuleType.job, "PAUSED", "IN_PROGRESS"),
        (ModuleType.job, "IN_PROGRESS", "COMPLETED"),
        (ModuleType.ticket, "OPEN", "DEVELOPMENT"),
        (ModuleType.ticket, "OPEN", "CUSTOMER_INPUT"),
        (ModuleType.ticket, "CUSTOMER_INPUT", "DEVELOPMENT"),
        (ModuleType.ticket, "DEVELOPMENT", "DESIGN_TEAM"),
        (ModuleType.ticket, "DESIGN_TEAM", "DEVELOPMENT"),
        (ModuleType.ticket, "DEVELOPMENT", "PUBLISHED"),
        (ModuleType.ticket, "PUBLISHED", "CLOSED"),
        (ModuleType.ticket, "OPEN", "FUTURE"),
        (ModuleType.ticket, "OPEN", "SUGGESTION"),
    ]
    for idx, (module, from_s, to_s) in enumerate(transitions, start=1):
        TRANSITION_MATRIX[idx] = {
            "transition_id": idx,
            "module": module,
            "from_status": from_s,
            "to_status": to_s,
            "allowed": True,
            "role": "Assigned User",
            "approval_required": to_s == "COMPLETED",
            "trigger_sla": True,
            "trigger_interconnect": True,
        }


_default_seed()


@router.get("/status-master")
def list_statuses(module: ModuleType | None = None, active: bool | None = None):
    rows = list(STATUS_MASTER.values())
    if module:
        rows = [r for r in rows if r["module"] == module]
    if active is not None:
        rows = [r for r in rows if r["active"] == active]
    return sorted(rows, key=lambda row: (row["module"], row["display_order"]))


@router.post("/status-master")
def create_status(payload: StatusDefinitionRequest):
    if payload.is_initial and any(r["module"] == payload.module and r["is_initial"] for r in STATUS_MASTER.values()):
        raise HTTPException(status_code=422, detail="Only one initial status is allowed per module")

    next_id = len(STATUS_MASTER) + 1
    row = {"status_id": next_id, **payload.model_dump()}
    STATUS_MASTER[next_id] = row
    _log_audit("STATUS_CREATED", row)
    return row


@router.patch("/status-master/{status_id}")
def update_status(status_id: int, payload: StatusDefinitionRequest):
    row = STATUS_MASTER.get(status_id)
    if not row:
        raise HTTPException(status_code=404, detail="Status not found")
    row.update(payload.model_dump())
    _log_audit("STATUS_UPDATED", {"status_id": status_id})
    return row


@router.delete("/status-master/{status_id}")
def delete_status(status_id: int):
    row = STATUS_MASTER.get(status_id)
    if not row:
        raise HTTPException(status_code=404, detail="Status not found")
    row["active"] = False
    _log_audit("STATUS_DEACTIVATED", {"status_id": status_id})
    return {"status": "deactivated", "status_id": status_id}


@router.get("/transition-matrix")
def list_transition_matrix(module: ModuleType | None = None):
    rows = list(TRANSITION_MATRIX.values())
    if module:
        rows = [r for r in rows if r["module"] == module]
    return rows


@router.post("/transition-matrix")
def create_transition(payload: TransitionRuleRequest):
    _resolve_status(payload.module, payload.from_status)
    _resolve_status(payload.module, payload.to_status)

    next_id = len(TRANSITION_MATRIX) + 1
    row = {"transition_id": next_id, **payload.model_dump()}
    TRANSITION_MATRIX[next_id] = row
    _log_audit("TRANSITION_CREATED", row)
    return row


@router.post("/{item_type}")
def create_work_item(item_type: WorkItemType, payload: WorkItemRequest):
    if payload.dependency_flag and not payload.dependency:
        raise HTTPException(status_code=422, detail="Dependency details are mandatory when dependency_flag is true")
    if payload.dependency and payload.dependency.dependency_type != item_type:
        raise HTTPException(status_code=422, detail="Cross-type dependency is not allowed in this baseline")

    if payload.dependency:
        parent = WORK_ITEMS[payload.dependency.dependency_type].get(payload.dependency.dependency_id)
        if not parent:
            raise HTTPException(status_code=422, detail="Dependency item not found")
        if parent["status"] != "COMPLETED":
            raise HTTPException(status_code=422, detail="Cannot create dependent item until parent is COMPLETED")
        if payload.start_date != parent["end_date"]:
            raise HTTPException(status_code=422, detail="Dependent start_date must equal parent end_date")

    next_id = len(WORK_ITEMS[item_type]) + 1
    initial_status = _initial_status(ModuleType(item_type.value))["status_name"]
    now = datetime.utcnow()
    due_at = _compute_sla_due(payload.priority, payload.showstopper, now)

    row = {
        "item_id": next_id,
        "item_type": item_type,
        **payload.model_dump(),
        "status": initial_status,
        "sla_started_at": now,
        "sla_due_at": due_at,
        "sla_paused_at": None,
        "paused_duration_minutes": 0,
        "sla_state": "RUNNING",
        "audit": [{"event": "CREATED", "at": now}],
    }
    WORK_ITEMS[item_type][next_id] = row

    _log_audit("WORK_ITEM_CREATED", {"item_type": item_type, "item_id": next_id, "priority": payload.priority})
    _emit_notification("TASK_CREATED" if item_type == WorkItemType.task else "JOB_CREATED", row, "Work item created")
    _emit_interconnect("CREATE_WORK_ITEM", row, {"trigger_sla": True})

    return row


@router.get("/{item_type}")
def list_work_items(item_type: WorkItemType, project_id: int | None = None):
    rows = list(WORK_ITEMS[item_type].values())
    if project_id is not None:
        rows = [r for r in rows if r["project_id"] == project_id]
    return rows


@router.patch("/{item_type}/{item_id}/status")
def change_status(item_type: WorkItemType, item_id: int, payload: StatusChangeRequest):
    row = WORK_ITEMS[item_type].get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Work item not found")

    transition_validation = validate_status_transition(
        module=ModuleType(item_type.value),
        from_status=row["status"],
        to_status=payload.status,
        actor_role=payload.actor_role,
        approval_granted=payload.approval_granted,
    )
    transition = transition_validation["transition"]
    new_status_def = transition_validation["next_status_def"]

    if new_status_def["pause_sla"]:
        row["sla_state"] = "PAUSED"
        row["sla_paused_at"] = datetime.utcnow()
    elif new_status_def["resume_sla"] and row["sla_paused_at"]:
        elapsed = datetime.utcnow() - row["sla_paused_at"]
        row["paused_duration_minutes"] += int(elapsed.total_seconds() // 60)
        row["sla_due_at"] = row["sla_due_at"] + elapsed
        row["sla_paused_at"] = None
        row["sla_state"] = "RUNNING"

    row["status"] = payload.status
    row["audit"].append(
        {
            "event": "STATUS_CHANGED",
            "from": transition["from_status"],
            "to": payload.status,
            "actor": payload.actor,
            "actor_role": payload.actor_role,
            "remark": payload.remark,
            "at": datetime.utcnow(),
        }
    )

    if datetime.utcnow() > row["sla_due_at"] and row["status"] != "COMPLETED":
        row["sla_state"] = "BREACHED"

    if transition["trigger_sla"]:
        _emit_interconnect("TRIGGER_SLA", row, {"from": transition["from_status"], "to": payload.status})
    if transition["trigger_interconnect"]:
        _emit_interconnect("STATUS_INTERCONNECT", row, {"from": transition["from_status"], "to": payload.status})

    if payload.status == "COMPLETED":
        for table in WORK_ITEMS.values():
            for candidate in table.values():
                dep = candidate.get("dependency")
                if dep and dep["dependency_type"] == item_type and dep["dependency_id"] == item_id:
                    _emit_notification(
                        "DEPENDENCY_READY",
                        candidate,
                        "Dependency completed. You can now start your task",
                    )

    _log_audit("WORK_ITEM_STATUS_CHANGED", {"item_type": item_type, "item_id": item_id, "to": payload.status})
    return row


@router.get("/sla/priority-rules")
def sla_priority_rules():
    return {
        "priority_duration_days": {"HIGH": 3, "MEDIUM": 3, "LOW": 7},
        "showstopper_override_hours": 24,
    }


@router.get("/notifications")
def notification_feed(event: str | None = None):
    rows = NOTIFICATION_EVENTS
    if event:
        rows = [r for r in rows if r["event"] == event]
    return rows


@router.get("/reports/status-transitions")
def status_transition_report():
    transitions = [
        {"item_type": row["item_type"], "item_id": row["item_id"], **event}
        for table in WORK_ITEMS.values()
        for row in table.values()
        for event in row["audit"]
        if event["event"] == "STATUS_CHANGED"
    ]
    return {"count": len(transitions), "rows": transitions}


@router.get("/reports/task-lifecycle")
def task_lifecycle_report():
    tasks = list(WORK_ITEMS[WorkItemType.task].values())
    return {
        "total_tasks": len(tasks),
        "completed": len([t for t in tasks if t["status"] == "COMPLETED"]),
        "in_progress": len([t for t in tasks if t["status"] == "IN_PROGRESS"]),
        "blocked": len([t for t in tasks if t["status"] == "PAUSED"]),
    }


@router.get("/reports/sla-vs-status")
def sla_vs_status_report():
    rows = [row for table in WORK_ITEMS.values() for row in table.values()]
    return {
        "total": len(rows),
        "running": len([r for r in rows if r["sla_state"] == "RUNNING"]),
        "paused": len([r for r in rows if r["sla_state"] == "PAUSED"]),
        "breached": len([r for r in rows if r["sla_state"] == "BREACHED"]),
    }


@router.get("/reports/dependency")
def dependency_report():
    rows = [
        {
            "item_type": row["item_type"],
            "item_id": row["item_id"],
            "dependency": row.get("dependency"),
            "dependency_ready": _dependency_ready(row["dependency"]["dependency_type"], row["dependency"]["dependency_id"])
            if row.get("dependency")
            else True,
        }
        for table in WORK_ITEMS.values()
        for row in table.values()
        if row.get("dependency")
    ]
    return {"count": len(rows), "rows": rows}


@router.get("/analytics")
def analytics_summary():
    durations: dict[str, list[float]] = defaultdict(list)
    status_counts: dict[str, int] = defaultdict(int)

    for table in WORK_ITEMS.values():
        for item in table.values():
            history = [event for event in item["audit"] if event["event"] == "STATUS_CHANGED"]
            status_counts[item["status"]] += 1
            for event in history:
                durations[event["to"]].append(1.0)

    avg_time = {status: sum(vals) / len(vals) for status, vals in durations.items()}
    bottlenecks = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "average_time_per_status": avg_time,
        "bottleneck_analysis": bottlenecks,
        "delay_reasons": ["Dependency Not Met", "Approval Pending", "SLA Pause"],
        "sla_compliance_pct": 0 if not status_counts else round(100 - (sla_vs_status_report()["breached"] * 100 / max(1, len(status_counts))), 2),
    }


@router.get("/project-linkage/{project_id}")
def project_linkage(project_id: int):
    return _project_rollup(project_id)


@router.get("/audit-log")
def audit_log():
    return AUDIT_LOG


@router.get("/interconnect-events")
def interconnect_events():
    return INTERCONNECT_EVENTS
