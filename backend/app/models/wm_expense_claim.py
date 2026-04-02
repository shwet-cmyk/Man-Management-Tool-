from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, ForeignKey, String

from app.database.session import Base


class WmExpenseClaim(Base):
    __tablename__ = "wm_expense_claim"

    claim_id = Column(BIGINT, primary_key=True, autoincrement=True)
    claim_no = Column(String(50), nullable=False, unique=True, index=True)
    claim_type = Column(String(30), nullable=False)
    expense_type = Column(String(50), nullable=False)

    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)

    emp_id = Column(BIGINT, nullable=False)
    entered_for_emp_id = Column(BIGINT, nullable=True)

    job_id = Column(BIGINT, ForeignKey("wm_job.job_id"), nullable=True)
    task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=True)
    task_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=True)
    timesheet_id = Column(BIGINT, ForeignKey("wm_timesheet.timesheet_id"), nullable=True)

    customer_id = Column(BIGINT, nullable=True)
    cost_center_id = Column(BIGINT, nullable=True)

    expense_date = Column(Date, nullable=False)
    amount = Column(DECIMAL(14, 2), nullable=False)
    tax_amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    total_amount = Column(DECIMAL(14, 2), nullable=False)
    recoverable_flag = Column(Boolean, nullable=False, default=False)

    vendor_payee_name = Column(String(255), nullable=True)
    remarks = Column(String(1000), nullable=True)
    approval_status = Column(String(20), nullable=False, default="Draft")
    submitted_by = Column(BIGINT, nullable=True)
    submitted_on = Column(DateTime, nullable=True)
    approved_by = Column(BIGINT, nullable=True)
    approved_on = Column(DateTime, nullable=True)
    rejected_by = Column(BIGINT, nullable=True)
    rejected_on = Column(DateTime, nullable=True)
    rejection_reason = Column(String(1000), nullable=True)
    voucher_id = Column(BIGINT, nullable=True)
    conversion_status = Column(String(30), nullable=False, default="Not Converted")
    converted_by = Column(BIGINT, nullable=True)
    converted_on = Column(DateTime, nullable=True)
    conversion_error = Column(String, nullable=True)

    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
