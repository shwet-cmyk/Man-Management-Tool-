from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, DECIMAL, String

from app.database.session import Base


class WmRbacUserAccessProfile(Base):
    __tablename__ = "wm_rbac_user_access_profile"

    user_id = Column(BIGINT, primary_key=True)
    linked_employee_id = Column(BIGINT, nullable=True, index=True)
    linked_account_head_id = Column(BIGINT, nullable=True)
    approval_required_flag = Column(Boolean, nullable=False, default=False)
    access_type = Column(String(40), nullable=False, default="ANYWHERE")
    two_factor_email_flag = Column(Boolean, nullable=False, default=False)
    sms_flag = Column(Boolean, nullable=False, default=False)
    max_discount = Column(DECIMAL(10, 2), nullable=True)
    backdated_entries_access = Column(String(40), nullable=False, default="NONE")
    backdated_days_limit = Column(BIGINT, nullable=True)
    agent_level = Column(String(40), nullable=False, default="SELF_ONLY")
    entries_of_all = Column(Boolean, nullable=False, default=False)
    entries_of_self_only = Column(Boolean, nullable=False, default=True)
    entries_of_self_and_downline = Column(Boolean, nullable=False, default=False)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_on = Column(DateTime, nullable=True)
