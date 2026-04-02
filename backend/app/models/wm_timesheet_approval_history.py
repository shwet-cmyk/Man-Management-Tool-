from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmTimesheetApprovalHistory(Base):
    __tablename__ = "wm_timesheet_approval_history"

    timesheet_approval_history_id = Column(BIGINT, primary_key=True, autoincrement=True)
    timesheet_id = Column(BIGINT, nullable=False, index=True)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    action_code = Column(String(20), nullable=False)
    decision_note = Column(String(1000), nullable=True)
    acted_by = Column(BIGINT, nullable=False)
    acted_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    override_flag = Column(Boolean, nullable=False, default=False)
    override_reason = Column(String(1000), nullable=True)
