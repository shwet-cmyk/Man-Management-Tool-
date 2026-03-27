from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, ForeignKey, String, Text

from app.database.session import Base


class WmTimesheet(Base):
    __tablename__ = "wm_timesheet"

    timesheet_id = Column(BIGINT, primary_key=True, autoincrement=True)
    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    customer_id = Column(BIGINT, nullable=True)

    job_id = Column(BIGINT, ForeignKey("wm_job.job_id"), nullable=False, index=True)
    task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=True, index=True)
    task_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=True, index=True)

    emp_id = Column(BIGINT, nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    hours = Column(DECIMAL(10, 2), nullable=False)
    billable_hours = Column(DECIMAL(10, 2), nullable=False, default=0)
    overtime_hours = Column(DECIMAL(10, 2), nullable=False, default=0)

    activity_type = Column(String(50), nullable=True)
    remarks = Column(String(1000), nullable=True)
    attachment_ref = Column(String(1000), nullable=True)
    expense_link_id = Column(BIGINT, nullable=True)
    reimbursement_link_id = Column(BIGINT, nullable=True)

    approval_status = Column(String(20), nullable=False, default="Draft")
    submitted_by = Column(BIGINT, nullable=True)
    submitted_on = Column(DateTime, nullable=True)
    approved_by = Column(BIGINT, nullable=True)
    approved_on = Column(DateTime, nullable=True)
    rejected_by = Column(BIGINT, nullable=True)
    rejected_on = Column(DateTime, nullable=True)
    rejection_reason = Column(String(1000), nullable=True)
    entered_for_emp_id = Column(BIGINT, nullable=True)

    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
