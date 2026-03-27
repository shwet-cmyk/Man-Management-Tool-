from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, String, Text

from app.database.session import Base


class WmJob(Base):
    __tablename__ = "wm_job"

    job_id = Column(BIGINT, primary_key=True, autoincrement=True)
    job_no = Column(String(50), nullable=False, unique=True, index=True)

    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)

    customer_id = Column(BIGINT, nullable=False)
    service_id = Column(BIGINT, nullable=True)

    job_name = Column(String(255), nullable=False)
    priority = Column(String(20), nullable=True)

    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)

    planned_hours = Column(DECIMAL(10, 2), nullable=True)
    planned_minutes = Column(BIGINT, nullable=True)
    planned_amount = Column(DECIMAL(18, 2), nullable=True)

    is_billable = Column(Boolean, nullable=False, default=True)

    manager_id = Column(BIGINT, nullable=True)

    execution_status = Column(String(20), nullable=False, default="Open")
    billing_status = Column(String(20), nullable=False, default="Not Billed")

    remarks = Column(Text, nullable=True)
    is_recurring = Column(Boolean, nullable=False, default=False)

    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
