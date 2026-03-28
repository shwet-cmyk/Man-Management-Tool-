from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmEmployeeGroup(Base):
    __tablename__ = "wm_employee_group"

    employee_group_id = Column(BIGINT, primary_key=True, autoincrement=True)
    group_code = Column(String(40), nullable=False, unique=True, index=True)
    group_name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
