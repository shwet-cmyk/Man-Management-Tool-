from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, ForeignKey

from app.database.session import Base


class WmEmployeeGroupMember(Base):
    __tablename__ = "wm_employee_group_member"

    group_member_id = Column(BIGINT, primary_key=True, autoincrement=True)
    employee_group_id = Column(BIGINT, ForeignKey("wm_employee_group.employee_group_id"), nullable=False, index=True)
    emp_id = Column(BIGINT, nullable=False, index=True)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
