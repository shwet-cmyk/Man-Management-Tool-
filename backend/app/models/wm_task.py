from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class WmTask(Base):
    __tablename__ = "wm_task"

    task_id = Column(BIGINT, primary_key=True, autoincrement=True)
    task_no = Column(String(50), nullable=False, unique=True, index=True)
    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    customer_id = Column(BIGINT, nullable=True)
    job_id = Column(BIGINT, nullable=True)
    client_name = Column(String(255), nullable=True)
    project_id = Column(BIGINT, nullable=True)
    cost_center_id = Column(BIGINT, nullable=True)
    parent_task_id = Column(BIGINT, nullable=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    product = Column(String(150), nullable=True)
    category = Column(String(150), nullable=True)
    task_type = Column(String(30), nullable=False)
    priority_code = Column(String(20), nullable=False)
    status_code = Column(String(30), nullable=False)

    primary_owner_emp_id = Column(BIGINT, nullable=False)
    manager_emp_id = Column(BIGINT, nullable=True)
    reviewer_emp_id = Column(BIGINT, nullable=True)

    billable_flag = Column(Boolean, nullable=False)
    billed_amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    estimated_hours = Column(DECIMAL(12, 2), nullable=False)
    actual_hours_rollup = Column(DECIMAL(12, 2), nullable=False, default=0)
    total_direct_cost = Column(DECIMAL(14, 2), nullable=False, default=0)
    total_cost_to_company = Column(DECIMAL(14, 2), nullable=False, default=0)
    total_overhead_amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    total_cost_with_overhead = Column(DECIMAL(14, 2), nullable=False, default=0)
    total_billed_amount = Column(DECIMAL(14, 2), nullable=False, default=0)
    total_profit_or_loss = Column(DECIMAL(14, 2), nullable=False, default=0)
    financial_status = Column(String(30), nullable=False, default="Billable Pending")
    progress_percent = Column(DECIMAL(5, 2), nullable=False, default=0)
    total_job_count = Column(Integer, nullable=False, default=0)
    completed_job_count = Column(Integer, nullable=False, default=0)
    pending_job_count = Column(Integer, nullable=False, default=0)
    blocked_job_count = Column(Integer, nullable=False, default=0)
    rollover_count_rollup = Column(Integer, nullable=False, default=0)
    critical_flag = Column(Boolean, nullable=False, default=False)
    remarks = Column(String(1000), nullable=True)

    planned_start = Column(DateTime, nullable=False)
    due_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)

    workflow_id = Column(BIGINT, nullable=True)
    workflow_state_code = Column(String(30), nullable=True)

    source_type = Column(String(20), nullable=False, default="MANUAL")
    source_ticket_id = Column(BIGINT, nullable=True)
    source_reference = Column(String(100), nullable=True)

    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    assignments = relationship("WmTaskAssignment", back_populates="task")
    participants = relationship("WmTaskParticipant", back_populates="task")
