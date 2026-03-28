from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, String

from app.database.session import Base


class WmBillingConfiguration(Base):
    __tablename__ = "wm_billing_configuration"

    billing_configuration_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(30), nullable=False)
    job_id = Column(BIGINT, nullable=True, index=True)
    task_id = Column(BIGINT, nullable=True, index=True)
    customer_id = Column(BIGINT, nullable=False)
    billable_flag = Column(Boolean, nullable=False, default=False)
    billing_model = Column(String(30), nullable=False)
    fixed_billing_amount = Column(DECIMAL(14, 2), nullable=True)
    billing_status = Column(String(30), nullable=False, default="Not Billable")
    billing_remarks = Column(String(1000), nullable=True)
    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
