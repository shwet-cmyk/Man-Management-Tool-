from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.event_bus import publish_event
from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry

router = APIRouter(prefix="/workflow-templates", tags=["Workflow Template Library"])


class TemplateTask(BaseModel):
    name: str
    default_duration_days: int = 1
    depends_on: list[str] = Field(default_factory=list)


class WorkflowTemplateCreateRequest(BaseModel):
    template_name: str
    template_type: str
    phases: list[str] = Field(default_factory=list)
    tasks: list[TemplateTask] = Field(default_factory=list)


TEMPLATES: dict[int, dict] = {}


@router.post("")
def create_template(payload: WorkflowTemplateCreateRequest):
    template_id = len(TEMPLATES) + 1
    row = {
        "template_id": template_id,
        **payload.model_dump(),
        "created_at": datetime.utcnow(),
    }
    TEMPLATES[template_id] = row
    add_audit_entry(
        AuditCreateRequest(
            user_name="SYSTEM",
            module="WORKFLOW_TEMPLATE",
            reference_id=str(template_id),
            action_type="CREATE",
            new_value={"template_name": payload.template_name},
        )
    )
    publish_event("WORKFLOW_TEMPLATE_CREATED", {"template_id": template_id})
    return row


@router.get("")
def list_templates(template_type: str | None = None):
    rows = list(TEMPLATES.values())
    if template_type:
        rows = [r for r in rows if r["template_type"].lower() == template_type.lower()]
    return rows


@router.post("/{template_id}/apply")
def apply_template(template_id: int, project_id: int):
    template = TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    generated = {
        "project_id": project_id,
        "phases": template["phases"],
        "tasks": [
            {
                "name": t["name"],
                "depends_on": t["depends_on"],
                "suggested_start_offset_days": idx * max(1, t["default_duration_days"]),
            }
            for idx, t in enumerate(template["tasks"])
        ],
    }
    publish_event("WORKFLOW_TEMPLATE_APPLIED", {"template_id": template_id, "project_id": project_id})
    return generated
