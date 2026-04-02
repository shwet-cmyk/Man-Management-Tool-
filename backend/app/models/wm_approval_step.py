from sqlalchemy import BIGINT, Boolean, Column, String, Text

from app.database.session import Base


class WmApprovalStep(Base):
    __tablename__ = "wm_approval_step"

    approval_step_id = Column(BIGINT, primary_key=True, autoincrement=True)
    approval_workflow_id = Column(BIGINT, nullable=False, index=True)
    step_order = Column(BIGINT, nullable=False, index=True)
    approver_type = Column(String(20), nullable=False)  # USER / ROLE
    approver_id = Column(BIGINT, nullable=False)
    is_parallel = Column(Boolean, nullable=False, default=False)
    dependency_step_id = Column(BIGINT, nullable=True)
    condition_json = Column(Text, nullable=True)
