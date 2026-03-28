from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, String, Text

from app.database.session import Base


class WmProject(Base):
    __tablename__ = "wm_project"

    project_id = Column(BIGINT, primary_key=True, autoincrement=True)
    project_code = Column(String(50), nullable=False, unique=True, index=True)
    project_name = Column(String(255), nullable=False)
    project_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    client_id = Column(BIGINT, nullable=True)
    client_name = Column(String(255), nullable=True)
    billable_flag = Column(Boolean, nullable=False, default=False)
    status = Column(String(30), nullable=False, default="Draft")
    priority = Column(String(20), nullable=False, default="Medium")
    owner_id = Column(BIGINT, nullable=False)
    owner_name = Column(String(255), nullable=False)
    manager_id = Column(BIGINT, nullable=True)
    manager_name = Column(String(255), nullable=True)
    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    budget_amount = Column(DECIMAL(14, 2), nullable=True)
    billed_amount_rollup = Column(DECIMAL(14, 2), nullable=False, default=0)
    cost_to_company_rollup = Column(DECIMAL(14, 2), nullable=False, default=0)
    profit_or_loss_rollup = Column(DECIMAL(14, 2), nullable=False, default=0)
    progress_percent = Column(DECIMAL(5, 2), nullable=False, default=0)
    task_count = Column(BIGINT, nullable=False, default=0)
    job_count = Column(BIGINT, nullable=False, default=0)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
