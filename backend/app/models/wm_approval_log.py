from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmApprovalLog(Base):
    __tablename__ = "wm_approval_log"

    approval_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    approval_transaction_id = Column(BIGINT, nullable=False, index=True)
    approval_step_id = Column(BIGINT, nullable=False, index=True)
    user_id = Column(BIGINT, nullable=False, index=True)
    action = Column(String(20), nullable=False)  # APPROVED / REJECTED / SYSTEM
    remarks = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
