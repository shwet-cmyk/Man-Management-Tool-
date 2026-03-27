from sqlalchemy import BIGINT, Column, String

from app.database.session import Base


class WmApprovalRule(Base):
    __tablename__ = "wm_approval_rule"

    approval_rule_id = Column(BIGINT, primary_key=True, autoincrement=True)
    approval_workflow_id = Column(BIGINT, nullable=False, index=True)
    condition_type = Column(String(20), nullable=False)  # AMOUNT / FIELD
    operator = Column(String(10), nullable=False)
    value = Column(String(200), nullable=False)
    field_name = Column(String(100), nullable=True)
