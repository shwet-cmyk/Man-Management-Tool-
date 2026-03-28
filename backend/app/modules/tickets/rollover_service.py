from __future__ import annotations

from datetime import datetime

from app.models.wm_task_rollover_history import WmTaskRolloverHistory


class RolloverService:
    def __init__(self, db):
        self.db = db

    def register_rollover(self, task_id: int, previous_due_at, revised_due_at, changed_by: int, reason: str, remarks: str | None = None):
        count = self.db.query(WmTaskRolloverHistory).filter(WmTaskRolloverHistory.task_id == task_id).count() + 1
        approval_required = count >= 3
        row = WmTaskRolloverHistory(
            task_id=task_id,
            previous_due_at=previous_due_at,
            revised_due_at=revised_due_at,
            changed_by=changed_by,
            changed_at=datetime.utcnow(),
            reason=reason,
            approval_required=approval_required,
            approval_status="PENDING" if approval_required else "NOT_REQUIRED",
            remarks=remarks,
        )
        self.db.add(row)
        return {"rollover_id": row.rollover_id, "rollover_count": count, "is_critical": count >= 3}
