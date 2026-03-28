from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmTimesheetReimbursementLine(Base):
    __tablename__ = "wm_timesheet_reimbursement_line"

    reimbursement_line_id = Column(BIGINT, primary_key=True, autoincrement=True)
    timesheet_id = Column(BIGINT, ForeignKey("wm_timesheet.timesheet_id"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
