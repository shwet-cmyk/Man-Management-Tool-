from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.users.router import _USERS

router = APIRouter(prefix="/approvals", tags=["Approval Engine"])


class ApprovalModule(str, Enum):
    task = "TASK"
    job = "JOB"
    timesheet = "TIMESHEET"
    billing = "BILLING"
    rollover = "ROLLOVER"
    cost = "COST"


class ApprovalState(str, Enum):
    pending_l1 = "PENDING_LEVEL_1"
    pending_l2 = "PENDING_LEVEL_2"
    approved = "APPROVED"
    rejected = "REJECTED"
    sent_back = "SENT_BACK"
    rework_required = "REWORK_REQUIRED"
    auto_approved = "AUTO_APPROVED"


class ApprovalConfigRequest(BaseModel):
    module: ApprovalModule
    approval_required: bool = True
    level2_role: str = "Department POC"
    auto_approve_after_escalation: bool = False
    escalation_hours: int = Field(default=24, gt=0)


class ApprovalTriggerRequest(BaseModel):
    module: ApprovalModule
    reference_id: int
    creator_user_id: int
    employee_name: str
    project_name: str | None = None
    context: dict = Field(default_factory=dict)


class ApprovalActionRequest(BaseModel):
    actor_user_id: int
    actor_role: str
    action: str  # APPROVE / REJECT / SEND_BACK
    remarks: str | None = None


class ResubmitRequest(BaseModel):
    creator_user_id: int
    modification_note: str


APPROVAL_CONFIGS: dict[ApprovalModule, dict] = {
    ApprovalModule.task: ApprovalConfigRequest(module=ApprovalModule.task).model_dump(),
    ApprovalModule.job: ApprovalConfigRequest(module=ApprovalModule.job).model_dump(),
    ApprovalModule.timesheet: ApprovalConfigRequest(module=ApprovalModule.timesheet).model_dump(),
    ApprovalModule.billing: ApprovalConfigRequest(module=ApprovalModule.billing).model_dump(),
    ApprovalModule.rollover: ApprovalConfigRequest(module=ApprovalModule.rollover).model_dump(),
    ApprovalModule.cost: ApprovalConfigRequest(module=ApprovalModule.cost, approval_required=False).model_dump(),
}
APPROVALS: dict[int, dict] = {}
APPROVAL_AUDIT: list[dict] = []
APPROVAL_NOTIFICATIONS: list[dict] = []


def _log(event: str, payload: dict):
    APPROVAL_AUDIT.append({"event": event, "at": datetime.utcnow(), **payload})


def _user_needs_approval(user_id: int) -> bool:
    user = _USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=422, detail="Creator user not found")
    return bool(user.get("approval_required", True))


def _manager_of(user_id: int) -> int | None:
    user = _USERS.get(user_id)
    return user.get("reporting_to") if user else None


def trigger_approval_request(payload: ApprovalTriggerRequest) -> dict:
    config = APPROVAL_CONFIGS[payload.module]

    if not config["approval_required"] or not _user_needs_approval(payload.creator_user_id):
        result = {
            "approval_id": None,
            "state": ApprovalState.auto_approved,
            "final": True,
            "message": "Auto-approved based on config/user toggle",
        }
        _log("APPROVAL_AUTO_APPROVED", {"module": payload.module, "reference_id": payload.reference_id})
        return result

    next_id = len(APPROVALS) + 1
    manager_id = _manager_of(payload.creator_user_id)
    record = {
        "approval_id": next_id,
        **payload.model_dump(),
        "state": ApprovalState.pending_l1,
        "level1_approver_user_id": manager_id,
        "level2_role": config["level2_role"],
        "level1_approved_by": None,
        "level2_approved_by": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "history": [],
    }
    APPROVALS[next_id] = record
    APPROVAL_NOTIFICATIONS.append(
        {
            "event": "APPROVAL_REQUIRED",
            "approval_id": next_id,
            "to_user_id": manager_id,
            "module": payload.module,
            "reference_id": payload.reference_id,
            "at": datetime.utcnow(),
        }
    )
    _log("APPROVAL_CREATED", {"approval_id": next_id, "module": payload.module, "reference_id": payload.reference_id})
    return {"approval_id": next_id, "state": ApprovalState.pending_l1, "final": False}


@router.get("/config")
def list_approval_config():
    return APPROVAL_CONFIGS


@router.put("/config/{module}")
def update_approval_config(module: ApprovalModule, payload: ApprovalConfigRequest):
    APPROVAL_CONFIGS[module] = payload.model_dump()
    _log("APPROVAL_CONFIG_UPDATED", {"module": module})
    return APPROVAL_CONFIGS[module]


@router.post("/trigger")
def trigger_approval(payload: ApprovalTriggerRequest):
    return trigger_approval_request(payload)


@router.get("/inbox")
def approval_inbox(
    module: ApprovalModule | None = None,
    employee: str | None = None,
    pending_level: str | None = None,
):
    rows = list(APPROVALS.values())
    if module:
        rows = [r for r in rows if r["module"] == module]
    if employee:
        rows = [r for r in rows if r["employee_name"] == employee]
    if pending_level:
        rows = [r for r in rows if r["state"] == pending_level]
    return rows


@router.get("/{approval_id}")
def approval_detail(approval_id: int):
    row = APPROVALS.get(approval_id)
    if not row:
        raise HTTPException(status_code=404, detail="Approval record not found")
    return row


@router.post("/{approval_id}/action")
def approval_action(approval_id: int, payload: ApprovalActionRequest):
    row = APPROVALS.get(approval_id)
    if not row:
        raise HTTPException(status_code=404, detail="Approval record not found")

    action = payload.action.upper()
    if action in {"REJECT", "SEND_BACK"} and not payload.remarks:
        raise HTTPException(status_code=422, detail="Remarks mandatory for Reject/Send Back")

    current_state = row["state"]
    allowed_admin = payload.actor_role in {"Admin", "Super Admin"}

    if current_state == ApprovalState.pending_l1:
        if not allowed_admin and payload.actor_user_id != row["level1_approver_user_id"]:
            raise HTTPException(status_code=403, detail="Only reporting manager can approve at Level 1")

        if action == "APPROVE":
            row["state"] = ApprovalState.pending_l2
            row["level1_approved_by"] = payload.actor_user_id
            APPROVAL_NOTIFICATIONS.append(
                {
                    "event": "APPROVAL_L2_REQUIRED",
                    "approval_id": approval_id,
                    "to_role": row["level2_role"],
                    "at": datetime.utcnow(),
                }
            )
        elif action in {"REJECT", "SEND_BACK"}:
            row["state"] = ApprovalState.sent_back
            APPROVAL_NOTIFICATIONS.append(
                {
                    "event": "APPROVAL_REJECTED_L1",
                    "approval_id": approval_id,
                    "to_user_id": row["creator_user_id"],
                    "at": datetime.utcnow(),
                }
            )
        else:
            raise HTTPException(status_code=422, detail="Invalid action")

    elif current_state == ApprovalState.pending_l2:
        if not allowed_admin and payload.actor_role != row["level2_role"]:
            raise HTTPException(status_code=403, detail="Only Department POC can approve at Level 2")
        if action == "APPROVE":
            row["state"] = ApprovalState.approved
            row["level2_approved_by"] = payload.actor_user_id
            APPROVAL_NOTIFICATIONS.append(
                {
                    "event": "APPROVAL_COMPLETED",
                    "approval_id": approval_id,
                    "to_user_id": row["creator_user_id"],
                    "at": datetime.utcnow(),
                }
            )
        elif action in {"REJECT", "SEND_BACK"}:
            row["state"] = ApprovalState.sent_back
            row["level1_approved_by"] = None  # reset chain
            APPROVAL_NOTIFICATIONS.extend(
                [
                    {
                        "event": "APPROVAL_REJECTED_L2",
                        "approval_id": approval_id,
                        "to_user_id": row["creator_user_id"],
                        "at": datetime.utcnow(),
                    },
                    {
                        "event": "APPROVAL_REJECTED_L2_NOTIFY_L1",
                        "approval_id": approval_id,
                        "to_user_id": row["level1_approver_user_id"],
                        "at": datetime.utcnow(),
                    },
                ]
            )
        else:
            raise HTTPException(status_code=422, detail="Invalid action")
    else:
        raise HTTPException(status_code=422, detail="Approval is not actionable in current state")

    row["updated_at"] = datetime.utcnow()
    row["history"].append(
        {
            "level": "L1" if current_state == ApprovalState.pending_l1 else "L2",
            "action": action,
            "user": payload.actor_user_id,
            "role": payload.actor_role,
            "remarks": payload.remarks,
            "at": datetime.utcnow(),
            "previous_state": current_state,
            "new_state": row["state"],
        }
    )
    _log("APPROVAL_ACTION", {"approval_id": approval_id, "action": action, "new_state": row["state"]})
    return row


@router.post("/{approval_id}/resubmit")
def approval_resubmit(approval_id: int, payload: ResubmitRequest):
    row = APPROVALS.get(approval_id)
    if not row:
        raise HTTPException(status_code=404, detail="Approval record not found")
    if row["creator_user_id"] != payload.creator_user_id:
        raise HTTPException(status_code=403, detail="Only creator can resubmit")
    if row["state"] != ApprovalState.sent_back:
        raise HTTPException(status_code=422, detail="Only sent-back requests can be resubmitted")

    row["state"] = ApprovalState.pending_l1
    row["level1_approved_by"] = None
    row["level2_approved_by"] = None
    row["updated_at"] = datetime.utcnow()
    row["history"].append(
        {
            "level": "CREATOR",
            "action": "RESUBMIT",
            "user": payload.creator_user_id,
            "remarks": payload.modification_note,
            "at": datetime.utcnow(),
            "previous_state": ApprovalState.sent_back,
            "new_state": ApprovalState.pending_l1,
        }
    )
    APPROVAL_NOTIFICATIONS.append(
        {
            "event": "APPROVAL_RESUBMITTED",
            "approval_id": approval_id,
            "to_user_id": row["level1_approver_user_id"],
            "at": datetime.utcnow(),
        }
    )
    _log("APPROVAL_RESUBMITTED", {"approval_id": approval_id})
    return row


@router.post("/escalations/run")
def run_escalations():
    now = datetime.utcnow()
    escalations = []

    for row in APPROVALS.values():
        if row["state"] not in {ApprovalState.pending_l1, ApprovalState.pending_l2}:
            continue
        cfg = APPROVAL_CONFIGS[row["module"]]
        threshold = row["updated_at"] + timedelta(hours=cfg["escalation_hours"])
        if now < threshold:
            continue

        event = {
            "approval_id": row["approval_id"],
            "module": row["module"],
            "state": row["state"],
            "escalated_at": now,
        }
        escalations.append(event)

        if row["state"] == ApprovalState.pending_l1:
            APPROVAL_NOTIFICATIONS.extend(
                [
                    {"event": "ESCALATION_L1_MANAGER_MANAGER", "approval_id": row["approval_id"], "at": now},
                    {"event": "ESCALATION_L1_ADMIN", "approval_id": row["approval_id"], "at": now},
                ]
            )
        else:
            APPROVAL_NOTIFICATIONS.extend(
                [
                    {"event": "ESCALATION_L2_ADMIN", "approval_id": row["approval_id"], "at": now},
                    {"event": "ESCALATION_L2_SUPER_ADMIN", "approval_id": row["approval_id"], "at": now},
                ]
            )

        if cfg["auto_approve_after_escalation"]:
            row["state"] = ApprovalState.approved
            row["history"].append(
                {
                    "level": "SYSTEM",
                    "action": "AUTO_APPROVE",
                    "user": "SYSTEM",
                    "remarks": "Auto approved after escalation timeout",
                    "at": now,
                    "previous_state": event["state"],
                    "new_state": ApprovalState.approved,
                }
            )

        row["updated_at"] = now
        _log("APPROVAL_ESCALATED", event)

    return {"escalations": escalations, "count": len(escalations)}


@router.get("/reports/summary")
def approval_reports():
    rows = list(APPROVALS.values())
    pending = len([r for r in rows if r["state"] in {ApprovalState.pending_l1, ApprovalState.pending_l2}])
    rejected = len([r for r in rows if r["state"] == ApprovalState.rejected])
    sent_back = len([r for r in rows if r["state"] == ApprovalState.sent_back])
    return {
        "approval_pending_report": pending,
        "approval_tat_report_hours": [
            {
                "approval_id": r["approval_id"],
                "tat_hours": round((r["updated_at"] - r["created_at"]).total_seconds() / 3600, 2),
            }
            for r in rows
        ],
        "rejection_analysis": {"rejected": rejected, "sent_back": sent_back},
        "escalation_report": [e for e in APPROVAL_AUDIT if e["event"] == "APPROVAL_ESCALATED"],
    }


@router.get("/analytics/summary")
def approval_analytics():
    rows = list(APPROVALS.values())
    return {
        "approval_delay_trends": [
            {
                "approval_id": r["approval_id"],
                "hours_open": round((datetime.utcnow() - r["created_at"]).total_seconds() / 3600, 2),
            }
            for r in rows
            if r["state"] in {ApprovalState.pending_l1, ApprovalState.pending_l2}
        ],
        "manager_performance": {},
        "bottleneck_analysis": {
            "pending_l1": len([r for r in rows if r["state"] == ApprovalState.pending_l1]),
            "pending_l2": len([r for r in rows if r["state"] == ApprovalState.pending_l2]),
        },
    }


@router.get("/notifications")
def approval_notifications():
    return APPROVAL_NOTIFICATIONS


@router.get("/audit-log")
def approval_audit_log():
    return APPROVAL_AUDIT


@router.post("/approve")
def approve_action(approval_id: int, actor_user_id: int, actor_role: str, remarks: str | None = None):
    return approval_action(
        approval_id=approval_id,
        payload=ApprovalActionRequest(
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action="APPROVE",
            remarks=remarks,
        ),
    )
