from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.event_bus import publish_event
from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry
from app.modules.tasks.router import TASKS
from app.modules.tickets.router import TICKETS

router = APIRouter(prefix="/intake-forms", tags=["Request Intake Forms"])


class DynamicField(BaseModel):
    key: str
    label: str
    required: bool = False


class FormCreateRequest(BaseModel):
    form_name: str
    output_type: str
    default_assignee: str | None = None
    fields: list[DynamicField] = Field(default_factory=list)


class FormSubmissionRequest(BaseModel):
    submitted_by: str
    values: dict[str, Any]


FORMS: dict[int, dict] = {}


@router.post("")
def create_form(payload: FormCreateRequest):
    output = payload.output_type.upper()
    if output not in {"TICKET", "TASK"}:
        raise HTTPException(status_code=422, detail="output_type must be TICKET or TASK")

    form_id = len(FORMS) + 1
    row = {
        "form_id": form_id,
        **payload.model_dump(),
        "output_type": output,
        "created_at": datetime.utcnow(),
        "submissions": [],
    }
    FORMS[form_id] = row
    add_audit_entry(
        AuditCreateRequest(
            user_name="SYSTEM",
            module="INTAKE_FORM",
            reference_id=str(form_id),
            action_type="CREATE",
            new_value={"form_name": payload.form_name, "output_type": output},
        )
    )
    return row


@router.post("/{form_id}/submit")
def submit_form(form_id: int, payload: FormSubmissionRequest):
    form = FORMS.get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    missing = [f["key"] for f in form["fields"] if f["required"] and f["key"] not in payload.values]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required fields: {missing}")

    generated_id = None
    if form["output_type"] == "TICKET":
        generated_id = len(TICKETS) + 1
    elif form["output_type"] == "TASK":
        generated_id = len(TASKS) + 1

    submission = {
        "submission_id": len(form["submissions"]) + 1,
        "submitted_by": payload.submitted_by,
        "values": payload.values,
        "generated_output_type": form["output_type"],
        "generated_reference_id": generated_id,
        "submitted_at": datetime.utcnow(),
    }
    form["submissions"].append(submission)
    publish_event(
        "INTAKE_SUBMITTED",
        {"form_id": form_id, "output_type": form["output_type"], "reference_id": generated_id},
    )
    return submission
