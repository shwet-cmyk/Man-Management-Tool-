from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, String

from app.database.session import Base


class WmBillingReadiness(Base):
    __tablename__ = "wm_billing_readiness"

    billing_readiness_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(30), nullable=False)
    job_id = Column(BIGINT, nullable=True, index=True)
    task_id = Column(BIGINT, nullable=True, index=True)
    ready_for_billing_flag = Column(Boolean, nullable=False, default=False)
    ready_for_billing_date = Column(DateTime, nullable=True)
    included_billable_hours = Column(DECIMAL(14, 2), nullable=False, default=0)
    included_recoverable_expense = Column(DECIMAL(14, 2), nullable=False, default=0)
    billing_status = Column(String(30), nullable=False, default="Billable")
    billing_remarks = Column(String(1000), nullable=True)
    marked_by = Column(BIGINT, nullable=False)
    marked_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
