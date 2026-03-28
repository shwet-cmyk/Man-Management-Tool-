from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmApprovalWorkflow(Base):
    __tablename__ = "wm_approval_workflow"

    approval_workflow_id = Column(BIGINT, primary_key=True, autoincrement=True)
    module_name = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
