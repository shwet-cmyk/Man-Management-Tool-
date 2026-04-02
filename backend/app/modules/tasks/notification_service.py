from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.wm_notification_queue import WmNotificationQueue


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def queue_task_notifications(self, task_id: int, recipients: list[int], message: str) -> None:
        unique_recipients = sorted(set(recipients))
        for emp_id in unique_recipients:
            self.db.add(
                WmNotificationQueue(
                    task_id=task_id,
                    recipient_emp_id=emp_id,
                    payload=message,
                    status="PENDING",
                )
            )
