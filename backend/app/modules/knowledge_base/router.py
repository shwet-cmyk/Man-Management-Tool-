from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.system_audit.router import AuditCreateRequest, add_audit_entry

router = APIRouter(prefix="/documentation", tags=["Documentation Module"])


class DocumentCreateRequest(BaseModel):
    title: str
    content: str
    linked_project_id: int | None = None
    linked_task_id: int | None = None
    author: str


DOCUMENTS: dict[int, dict] = {}


@router.post("")
def create_document(payload: DocumentCreateRequest):
    doc_id = len(DOCUMENTS) + 1
    row = {
        "document_id": doc_id,
        **payload.model_dump(),
        "version": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    DOCUMENTS[doc_id] = row
    add_audit_entry(
        AuditCreateRequest(
            user_name=payload.author,
            module="DOCUMENTATION",
            reference_id=str(doc_id),
            action_type="CREATE",
            new_value={"title": payload.title},
        )
    )
    return row


@router.get("")
def list_documents(linked_project_id: int | None = None, linked_task_id: int | None = None):
    rows = list(DOCUMENTS.values())
    if linked_project_id is not None:
        rows = [r for r in rows if r.get("linked_project_id") == linked_project_id]
    if linked_task_id is not None:
        rows = [r for r in rows if r.get("linked_task_id") == linked_task_id]
    return rows


@router.patch("/{document_id}")
def update_document(document_id: int, payload: DocumentCreateRequest):
    row = DOCUMENTS.get(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    old_content = row["content"]
    row.update(payload.model_dump())
    row["version"] += 1
    row["updated_at"] = datetime.utcnow()
    add_audit_entry(
        AuditCreateRequest(
            user_name=payload.author,
            module="DOCUMENTATION",
            reference_id=str(document_id),
            action_type="UPDATE",
            field_name="content",
            old_value=old_content,
            new_value=payload.content,
        )
    )
    return row
