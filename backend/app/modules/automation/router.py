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


class AutomationCreateRequest(BaseModel):
    automation_name: str
    module: str
    trigger_event: str
    trigger_scope: str | None = None
    condition_logic: str | None = None
    action_types: list[str] = Field(min_length=1)
    action_parameters: dict = Field(default_factory=dict)
    priority: int | None = None
    retry_policy: str | None = None
    failure_alert_to: list[str] = Field(default_factory=list)
    status: str = "DISABLED"


class AutomationTestRequest(BaseModel):
    test_context: dict = Field(default_factory=dict)


class AutomationPreviewRequest(BaseModel):
    sample_scope: dict = Field(default_factory=dict)


class AutomationRetryRequest(BaseModel):
    reason: str | None = None


RULES: dict[int, dict] = {}
TEMPLATES: dict[int, dict] = {}
RULE_EXECUTIONS: list[dict] = []
AUTOMATIONS: dict[int, dict] = {}
AUTOMATION_RUNS: dict[int, dict] = {}


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


@router.get("/list")
def automation_list(module: str | None = None, trigger_type: str | None = None, status: str | None = None):
    rows = list(AUTOMATIONS.values())
    if module:
        rows = [r for r in rows if r["module"].lower() == module.lower()]
    if trigger_type:
        rows = [r for r in rows if r["trigger_event"].lower() == trigger_type.lower()]
    if status:
        rows = [r for r in rows if r["status"].lower() == status.lower()]
    return rows


@router.post("/create")
def automation_create(payload: AutomationCreateRequest):
    if payload.priority is not None and payload.priority < 0:
        raise HTTPException(status_code=422, detail="Priority must be numeric and non-negative")
    next_id = len(AUTOMATIONS) + 1
    row = {
        "id": next_id,
        **payload.model_dump(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_run": None,
        "last_result": None,
        "failure_count": 0,
    }
    AUTOMATIONS[next_id] = row
    return row


@router.put("/update/{automation_id}")
def automation_update(automation_id: int, payload: AutomationCreateRequest):
    row = AUTOMATIONS.get(automation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    if payload.priority is not None and payload.priority < 0:
        raise HTTPException(status_code=422, detail="Priority must be numeric and non-negative")
    row.update(payload.model_dump())
    row["updated_at"] = datetime.utcnow()
    return row


@router.post("/enable/{automation_id}")
def automation_enable(automation_id: int):
    row = AUTOMATIONS.get(automation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    row["status"] = "ENABLED"
    row["updated_at"] = datetime.utcnow()
    return {"success": True, "id": automation_id, "status": row["status"]}


@router.post("/disable/{automation_id}")
def automation_disable(automation_id: int):
    row = AUTOMATIONS.get(automation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    row["status"] = "DISABLED"
    row["updated_at"] = datetime.utcnow()
    return {"success": True, "id": automation_id, "status": row["status"]}


@router.post("/clone/{automation_id}")
def automation_clone(automation_id: int):
    row = AUTOMATIONS.get(automation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    next_id = len(AUTOMATIONS) + 1
    clone = {**row, "id": next_id, "automation_name": f"{row['automation_name']} (Clone)", "status": "DISABLED"}
    AUTOMATIONS[next_id] = clone
    return clone


@router.post("/test/{automation_id}")
def automation_test(automation_id: int, payload: AutomationTestRequest):
    row = AUTOMATIONS.get(automation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    if not payload.test_context:
        raise HTTPException(status_code=422, detail="Test run parameters required")
    run_id = len(AUTOMATION_RUNS) + 1
    result = {
        "run_id": run_id,
        "automation_id": automation_id,
        "triggered_on": datetime.utcnow(),
        "trigger_event": row["trigger_event"],
        "execution_result": "SUCCESS",
        "affected_record": None,
        "duration_ms": 187,
        "retry_count": 0,
        "error_summary": None,
        "status": "COMPLETED",
    }
    AUTOMATION_RUNS[run_id] = result
    row["last_run"] = result["triggered_on"]
    row["last_result"] = result["execution_result"]
    return result


@router.post("/preview-impact/{automation_id}")
def automation_preview_impact(automation_id: int, payload: AutomationPreviewRequest):
    row = AUTOMATIONS.get(automation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return {
        "automation_id": automation_id,
        "estimated_affected_records": 12,
        "trigger_event": row["trigger_event"],
        "actions": row["action_types"],
        "sample_scope": payload.sample_scope,
    }


@router.get("/history/{automation_id}")
def automation_history(automation_id: int):
    if automation_id not in AUTOMATIONS:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    runs = [r for r in AUTOMATION_RUNS.values() if r["automation_id"] == automation_id]
    return {"automation_id": automation_id, "runs": runs}


@router.get("/run-detail/{run_id}")
def automation_run_detail(run_id: int):
    row = AUTOMATION_RUNS.get(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Run detail not found")
    return row


@router.post("/retry/{run_id}")
def automation_retry(run_id: int, payload: AutomationRetryRequest):
    row = AUTOMATION_RUNS.get(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Run detail not found")
    if row["execution_result"] != "FAILURE":
        raise HTTPException(status_code=422, detail="Retry allowed only on failed runs")
    if row.get("manual_retry_requested"):
        raise HTTPException(status_code=409, detail="Duplicate retry prevention: retry already requested")
    row["manual_retry_requested"] = True
    row["retry_reason"] = payload.reason
    return {"success": True, "run_id": run_id, "status": "RETRY_QUEUED"}
