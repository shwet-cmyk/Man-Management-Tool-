from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, String

from app.database.session import Base


class RefEmployee(Base):
    __tablename__ = "ref_employee"

    emp_id = Column(BIGINT, primary_key=True, index=True)
    employee_name = Column(String(255), nullable=False)
    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    designation = Column(String(120), nullable=True)
    manager_id = Column(BIGINT, nullable=True)
    shift_id = Column(BIGINT, nullable=True)
    holiday_calendar_id = Column(BIGINT, nullable=True)
    monthly_ctc = Column(DECIMAL(14, 2), nullable=False, default=0)
    hourly_cost = Column(DECIMAL(12, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_synced_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
