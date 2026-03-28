from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, ForeignKey, String, Text

from app.database.session import Base


class WmJob(Base):
    __tablename__ = "wm_job"

    job_id = Column(BIGINT, primary_key=True, autoincrement=True)
    job_no = Column(String(50), nullable=False, unique=True, index=True)

    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    parent_task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=True, index=True)

    customer_id = Column(BIGINT, nullable=False)
    client_name = Column(String(255), nullable=True)
    service_id = Column(BIGINT, nullable=True)

    job_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_employee_id = Column(BIGINT, nullable=True)
    assigned_employee_name = Column(String(255), nullable=True)
    assigned_manager_id = Column(BIGINT, nullable=True)
    assigned_manager_name = Column(String(255), nullable=True)
    priority = Column(String(20), nullable=True)

    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)

    planned_hours = Column(DECIMAL(10, 2), nullable=True)
    spent_hours = Column(DECIMAL(10, 2), nullable=False, default=0)
    planned_minutes = Column(BIGINT, nullable=True)
    estimated_amount = Column(DECIMAL(18, 2), nullable=True)

    is_billable = Column(Boolean, nullable=False, default=True)
    billed_amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    cost_to_company = Column(DECIMAL(14, 2), nullable=False, default=0)
    overhead_amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    final_cost_to_company = Column(DECIMAL(14, 2), nullable=False, default=0)
    profit_or_loss = Column(DECIMAL(14, 2), nullable=False, default=0)

    manager_id = Column(BIGINT, nullable=True)

    execution_status = Column(String(20), nullable=False, default="Open")
    progress_percent = Column(DECIMAL(5, 2), nullable=False, default=0)
    rollover_count = Column(BIGINT, nullable=False, default=0)
    critical_flag = Column(Boolean, nullable=False, default=False)
    dependency_mode = Column(String(30), nullable=False, default="FINISH_TO_START")
    dependency_job_id = Column(BIGINT, ForeignKey("wm_job.job_id"), nullable=True)
    dependency_completion_required = Column(Boolean, nullable=False, default=True)
    dependency_type = Column(String(30), nullable=False, default="FINISH_TO_START")
    dependency_mandatory_flag = Column(Boolean, nullable=False, default=True)
    dependency_status = Column(String(30), nullable=False, default="Not Required")
    dependency_completed_at = Column(DateTime, nullable=True)
    transfer_required = Column(Boolean, nullable=False, default=False)
    transfer_status = Column(String(30), nullable=False, default="Not Required")
    transfer_from_employee_id = Column(BIGINT, nullable=True)
    transfer_to_employee_id = Column(BIGINT, nullable=True)
    transfer_requested_at = Column(DateTime, nullable=True)
    transfer_accepted_at = Column(DateTime, nullable=True)
    transfer_rejected_at = Column(DateTime, nullable=True)
    transfer_rejection_reason = Column(String(1000), nullable=True)
    acceptance_required = Column(Boolean, nullable=False, default=True)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(BIGINT, nullable=True)
    billing_status = Column(String(20), nullable=False, default="Not Billed")

    remarks = Column(Text, nullable=True)
    is_recurring = Column(Boolean, nullable=False, default=False)

    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
