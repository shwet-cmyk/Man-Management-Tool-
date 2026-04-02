from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String, Text

from app.database.session import Base


class WmApprovalTransaction(Base):
    __tablename__ = "wm_approval_transaction"

    approval_transaction_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(BIGINT, nullable=False, index=True)
    approval_workflow_id = Column(BIGINT, nullable=False, index=True)
    status = Column(String(30), nullable=False, default="PENDING")
    current_step = Column(BIGINT, nullable=True)
    snapshot_json = Column(Text, nullable=False)
    accounting_triggered = Column(Boolean, nullable=False, default=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_on = Column(DateTime, nullable=True)
