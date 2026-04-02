from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.task_dependencies import TaskDependency
from app.modules.dependency_enforcement.schemas import DependencyActionRequest, DependencyCheckRequest, DependencyCreateRequest


class DependencyEnforcementService:
    def __init__(self, db: Session):
        self.db = db

    def create_dependency(self, payload: DependencyCreateRequest):
        self._ensure_not_circular(payload.task_id, payload.depends_on_task_id)
        row = TaskDependency(
            task_id=payload.task_id,
            user_id=payload.user_id,
            depends_on_user_id=payload.depends_on_user_id,
            depends_on_task_id=payload.depends_on_task_id,
            dependency_type=payload.dependency_type,
            status="PENDING",
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"dependency_id": row.id, "status": row.status}

    def check_dependency(self, payload: DependencyCheckRequest):
        if payload.override_flag and payload.action == "APPROVE":
            return {"allowed": True, "message": "Override allowed for approval action"}

        rows = self.db.query(TaskDependency).filter(TaskDependency.task_id == payload.task_id, TaskDependency.user_id == payload.user_id).all()
        for dep in rows:
            if dep.status != "APPROVED":
                return {"allowed": False, "message": f"Dependency pending approval from {dep.depends_on_user_id}"}
        return {"allowed": True, "message": "Dependency satisfied"}

    def transition_dependency(self, payload: DependencyActionRequest):
        row = self.db.query(TaskDependency).filter(TaskDependency.id == payload.dependency_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Dependency not found")

        if payload.action == "COMPLETE":
            row.status = "COMPLETED"
        elif payload.action == "APPROVE":
            if row.status != "COMPLETED":
                raise HTTPException(status_code=422, detail="Dependency can be approved only after completion")
            row.status = "APPROVED"
        else:
            row.status = "PENDING"

        if payload.action == "REJECT":
            self._reset_downstream(row.task_id)

        self.db.commit()
        return {"dependency_id": row.id, "status": row.status}

    def _ensure_not_circular(self, task_id: str, depends_on_task_id: str | None):
        if not depends_on_task_id:
            return
        if task_id == depends_on_task_id:
            raise HTTPException(status_code=422, detail="Circular dependency blocked")

        cursor = depends_on_task_id
        visited = {task_id}
        while cursor:
            if cursor in visited:
                raise HTTPException(status_code=422, detail="Circular dependency blocked")
            visited.add(cursor)
            next_row = self.db.query(TaskDependency).filter(TaskDependency.task_id == cursor).first()
            cursor = next_row.depends_on_task_id if next_row else None

    def _reset_downstream(self, task_id: str):
        rows = self.db.query(TaskDependency).filter(TaskDependency.depends_on_task_id == task_id).all()
        for row in rows:
            row.status = "PENDING"
