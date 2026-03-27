from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, String

from app.database.session import Base


class WmBillingDocumentLink(Base):
    __tablename__ = "wm_billing_document_link"

    billing_document_link_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(30), nullable=False)
    job_id = Column(BIGINT, nullable=True, index=True)
    task_id = Column(BIGINT, nullable=True, index=True)
    billing_reference_type = Column(String(30), nullable=False)
    billing_reference_id = Column(BIGINT, nullable=True)
    billing_reference_no = Column(String(100), nullable=True, index=True)
    billed_amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    billed_date = Column(Date, nullable=True)
    billing_status = Column(String(30), nullable=False)
    included_billable_hours = Column(DECIMAL(14, 2), nullable=False, default=0)
    included_recoverable_expense = Column(DECIMAL(14, 2), nullable=False, default=0)
    billing_remarks = Column(String(1000), nullable=True)
    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
