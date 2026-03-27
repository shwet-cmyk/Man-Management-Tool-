from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Column, DateTime, String

from app.database.session import Base


class WmBillingStatusHistory(Base):
    __tablename__ = "wm_billing_status_history"

    billing_status_history_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(30), nullable=False)
    job_id = Column(BIGINT, nullable=True, index=True)
    task_id = Column(BIGINT, nullable=True, index=True)
    old_billing_status = Column(String(30), nullable=False)
    new_billing_status = Column(String(30), nullable=False)
    action_code = Column(String(30), nullable=False)
    billing_reference_no = Column(String(100), nullable=True)
    billed_amount = Column(DECIMAL(14, 2), nullable=True)
    acted_by = Column(BIGINT, nullable=False)
    acted_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    remarks = Column(String(1000), nullable=True)
