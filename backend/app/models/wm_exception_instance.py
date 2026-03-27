from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, Integer, String

from app.database.session import Base


class WmExceptionInstance(Base):
    __tablename__ = "wm_exception_instance"

    exception_instance_id = Column(BIGINT, primary_key=True, autoincrement=True)
    exception_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(BIGINT, nullable=False)
    company_id = Column(BIGINT, nullable=True)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    customer_id = Column(BIGINT, nullable=True)
    job_id = Column(BIGINT, nullable=True)
    task_id = Column(BIGINT, nullable=True)
    task_participant_id = Column(BIGINT, nullable=True)
    emp_id = Column(BIGINT, nullable=True)
    manager_id = Column(BIGINT, nullable=True)
    planned_start = Column(DateTime, nullable=True)
    planned_due = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    planned_hours = Column(DECIMAL(14, 2), nullable=True)
    actual_hours = Column(DECIMAL(14, 2), nullable=True)
    billed_amount = Column(DECIMAL(14, 2), nullable=True)
    total_cost = Column(DECIMAL(14, 2), nullable=True)
    days_delayed = Column(Integer, nullable=True)
    exception_age_days = Column(Integer, nullable=True)
    exception_message = Column(String(1000), nullable=False)
    recommended_action = Column(String(1000), nullable=True)
    first_detected_on = Column(DateTime, nullable=False)
    last_evaluated_on = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    resolved_on = Column(DateTime, nullable=True)
    resolved_by = Column(BIGINT, nullable=True)
