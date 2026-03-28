from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String, Text

from app.database.session import Base


class WmTaskRolloverHistory(Base):
    __tablename__ = "wm_task_rollover_history"

    rollover_id = Column(BIGINT, primary_key=True, autoincrement=True)
    task_id = Column(BIGINT, nullable=False, index=True)
    previous_due_at = Column(DateTime, nullable=False)
    revised_due_at = Column(DateTime, nullable=False)
    changed_by = Column(BIGINT, nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Text, nullable=False)
    approval_required = Column(Boolean, nullable=False, default=False)
    approval_status = Column(String(20), nullable=False, default="NOT_REQUIRED")
    approved_by = Column(BIGINT, nullable=True)
    approval_at = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)
