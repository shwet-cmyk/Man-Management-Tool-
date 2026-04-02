from __future__ import annotations

from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/automation", tags=["Automation Engine"])


class EngineModule(str, Enum):
    task = "TASK"
    job = "JOB"
    ticket = "TICKET"
    project = "PROJECT"
    timesheet = "TIMESHEET"
    approval = "APPROVAL"


class TemplateType(str, Enum):
    email = "EMAIL"
    notification = "NOTIFICATION"
    alert = "ALERT"


class RuleTrigger(str, Enum):
    task_created = "TASK_CREATED"
    task_updated = "TASK_UPDATED"
    task_completed = "TASK_COMPLETED"
    job_created = "JOB_CREATED"
    job_completed = "JOB_COMPLETED"
    ticket_created = "TICKET_CREATED"
    ticket_status_changed = "TICKET_STATUS_CHANGED"
    sla_breach = "SLA_BREACH"
    approval_pending = "APPROVAL_PENDING"
    approval_rejected = "APPROVAL_REJECTED"
    timesheet_submitted = "TIMESHEET_SUBMITTED"


class ActionType(str, Enum):
    send_email = "SEND_EMAIL"
    create_task = "CREATE_TASK"
    update_status = "UPDATE_STATUS"
    assign_user = "ASSIGN_USER"
    trigger_notification = "TRIGGER_NOTIFICATION"
    add_remark = "ADD_REMARK"
    escalate = "ESCALATE"
    create_followup = "CREATE_FOLLOWUP"


VARIABLES_BY_MODULE = {
    "USER": ["#Employee Name#", "#Email#", "#Manager Name#"],
    "TASK": ["#Task Name#", "#Status#", "#Priority#", "#Due Date#", "#Delay Days#"],
    "JOB": ["#Job Name#", "#Assigned User#", "#Hours Logged#"],
    "PROJECT": ["#Project Name#", "#Phase#", "#Start Date#", "#End Date#", "#Completion %#"],
    "SLA": ["#SLA Status#", "#Remaining Time#", "#Breach Status#"],
    "COST": ["#Actual Cost#", "#Estimated Cost#", "#Profit#"],
    "TICKET": ["#Ticket Number#", "#Customer Name#", "#Issue#"],
}


class ConditionRequest(BaseModel):
    field: str
    operator: str
    value: str
    logic: str = "AND"


class RuleCreateRequest(BaseModel):
    rule_name: str
    module: EngineModule
    trigger: RuleTrigger
    conditions: list[ConditionRequest] = Field(default_factory=list)
    action: ActionType
    active: bool = True
    template_id: int | None = None


class TemplateCreateRequest(BaseModel):
    template_name: str
    module: EngineModule
    template_type: TemplateType
    subject: str | None = None
    body: str


class RuleExecutionRequest(BaseModel):
    trigger: RuleTrigger
    module: EngineModule
    payload: dict = Field(default_factory=dict)


RULES: dict[int, dict] = {}
TEMPLATES: dict[int, dict] = {}
RULE_EXECUTIONS: list[dict] = []


def _render_template(body: str, payload: dict) -> str:
    rendered = body
    for key, value in payload.items():
        rendered = rendered.replace(f"#{key}#", str(value))
    return rendered


@router.get("/variables")
def list_variables():
    return VARIABLES_BY_MODULE


@router.get("/templates")
def list_templates(module: EngineModule | None = None, template_type: TemplateType | None = None):
    rows = list(TEMPLATES.values())
    if module:
        rows = [r for r in rows if r["module"] == module]
    if template_type:
        rows = [r for r in rows if r["template_type"] == template_type]
    return rows


@router.post("/templates")
def create_template(payload: TemplateCreateRequest):
    next_id = len(TEMPLATES) + 1
    row = {"template_id": next_id, **payload.model_dump(), "updated_at": datetime.utcnow()}
    TEMPLATES[next_id] = row
    return row


@router.put("/templates/{template_id}")
def update_template(template_id: int, payload: TemplateCreateRequest):
    row = TEMPLATES.get(template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    row.update(payload.model_dump())
    row["updated_at"] = datetime.utcnow()
    return row


@router.delete("/templates/{template_id}")
def delete_template(template_id: int):
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    del TEMPLATES[template_id]
    return {"deleted": template_id}


@router.get("/rules")
def list_rules(module: EngineModule | None = None, active: bool | None = None):
    rows = list(RULES.values())
    if module:
        rows = [r for r in rows if r["module"] == module]
    if active is not None:
        rows = [r for r in rows if r["active"] == active]
    return rows


@router.post("/rules")
def create_rule(payload: RuleCreateRequest):
    if payload.action == ActionType.send_email and not payload.template_id:
        raise HTTPException(status_code=422, detail="Template required for email action")

    next_id = len(RULES) + 1
    row = {"rule_id": next_id, **payload.model_dump(), "last_run": None}
    RULES[next_id] = row
    return row


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, payload: RuleCreateRequest):
    row = RULES.get(rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    row.update(payload.model_dump())
    return row


@router.post("/rules/{rule_id}/clone")
def clone_rule(rule_id: int):
    row = RULES.get(rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    next_id = len(RULES) + 1
    clone = {**row, "rule_id": next_id, "rule_name": f"{row['rule_name']} (Clone)", "last_run": None}
    RULES[next_id] = clone
    return clone


@router.patch("/rules/{rule_id}/active")
def toggle_rule(rule_id: int, active: bool):
    row = RULES.get(rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    row["active"] = active
    return row


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int):
    if rule_id not in RULES:
        raise HTTPException(status_code=404, detail="Rule not found")
    del RULES[rule_id]
    return {"deleted": rule_id}


@router.post("/execute")
def execute_rules(payload: RuleExecutionRequest):
    matches = [
        r for r in RULES.values() if r["active"] and r["trigger"] == payload.trigger and r["module"] == payload.module
    ]
    executions = []

    for rule in matches:
        template_content = None
        rendered = None
        if rule.get("template_id"):
            template = TEMPLATES.get(rule["template_id"])
            if template:
                template_content = template
                rendered = _render_template(template["body"], payload.payload)

        record = {
            "rule_id": rule["rule_id"],
            "trigger": payload.trigger,
            "module": payload.module,
            "action": rule["action"],
            "template_id": rule.get("template_id"),
            "rendered_output": rendered,
            "payload": payload.payload,
            "executed_at": datetime.utcnow(),
            "status": "SUCCESS",
        }
        RULE_EXECUTIONS.append(record)
        rule["last_run"] = record["executed_at"]
        executions.append(record)

    return {"matched_rules": len(matches), "executions": executions}


@router.get("/reports/execution")
def execution_report():
    return {
        "rule_execution_report": RULE_EXECUTIONS,
        "failed_rule_report": [r for r in RULE_EXECUTIONS if r["status"] != "SUCCESS"],
        "template_usage_report": {
            tid: len([r for r in RULE_EXECUTIONS if r.get("template_id") == tid]) for tid in TEMPLATES.keys()
        },
    }


@router.get("/analytics/summary")
def automation_analytics():
    total_rules = len(RULES)
    total_runs = len(RULE_EXECUTIONS)
    return {
        "most_triggered_rules": sorted(
            [{"rule_id": rid, "runs": len([r for r in RULE_EXECUTIONS if r["rule_id"] == rid])} for rid in RULES.keys()],
            key=lambda x: x["runs"],
            reverse=True,
        ),
        "automation_efficiency": {"total_rules": total_rules, "total_runs": total_runs},
        "manual_vs_automated_actions": {"manual": 0, "automated": total_runs},
    }
