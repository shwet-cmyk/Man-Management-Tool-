from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Numeric, String

from app.database.session import Base


class WmRbacApprovalLimit(Base):
    __tablename__ = "wm_rbac_approval_limit"

    approval_limit_id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, nullable=False, index=True)
    module_name = Column(String(100), nullable=False, index=True)
    max_amount = Column(Numeric(18, 2), nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
