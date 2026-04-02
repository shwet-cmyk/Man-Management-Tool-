from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmWorkflowApproval(Base):
    __tablename__ = "wm_workflow_approval"

    approval_id = Column(BIGINT, primary_key=True, autoincrement=True)
    instance_id = Column(BIGINT, nullable=False, index=True)
    node_id = Column(BIGINT, nullable=False)
    approver_user_id = Column(BIGINT, nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")
    decision_group = Column(String(40), nullable=True)
    remarks = Column(Text, nullable=True)
    decided_on = Column(DateTime, nullable=True)
