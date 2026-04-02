from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.projects.router import PROJECTS
from app.modules.tasks.router import TASKS
from app.modules.tickets.router import TICKETS

router = APIRouter(prefix="/client-portal", tags=["Client Portal"])


class GuestLoginRequest(BaseModel):
    client_email: str
    project_id: int


@router.post("/guest-login")
def guest_login(payload: GuestLoginRequest):
    if payload.project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "access": "granted",
        "token": f"guest-{payload.project_id}-{payload.client_email}",
        "scope": {"project_id": payload.project_id, "permissions": ["VIEW_PROJECT", "VIEW_TASK", "RAISE_TICKET", "COMMENT"]},
    }


@router.get("/projects/{project_id}")
def project_snapshot(project_id: int):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = [t for t in TASKS.values() if t.get("project_id") == project_id]
    tickets = [t for t in TICKETS.values() if t.get("project_id") == project_id]
    return {
        "project": project,
        "tasks": [{"task_id": t["task_id"], "task_name": t["task_name"], "status": t["status"]} for t in tasks],
        "tickets": [{"ticket_id": t["ticket_id"], "title": t["title"], "status": t["status"]} for t in tickets],
    }


class ClientTicketCreateRequest(BaseModel):
    project_id: int
    title: str
    description: str
    created_by: str


@router.post("/tickets")
def raise_client_ticket(payload: ClientTicketCreateRequest):
    if payload.project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    ticket_id = len(TICKETS) + 1
    row = {
        "ticket_id": ticket_id,
        "project_id": payload.project_id,
        "title": payload.title,
        "description": payload.description,
        "status": "OPEN",
        "source": "CLIENT_PORTAL",
        "created_by": payload.created_by,
        "created_at": datetime.utcnow(),
    }
    TICKETS[ticket_id] = row
    return row
