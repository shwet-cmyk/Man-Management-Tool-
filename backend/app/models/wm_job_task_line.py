from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, Date, DateTime, ForeignKey, String, Text

from app.database.session import Base


class WmJobTaskLine(Base):
    __tablename__ = "wm_job_task_line"

    job_task_id = Column(BIGINT, primary_key=True, autoincrement=True)
    parent_job_id = Column(BIGINT, ForeignKey("wm_job.job_id"), nullable=False, index=True)
    line_no = Column(BIGINT, nullable=False)
    task_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_employee_id = Column(BIGINT, nullable=True)
    planned_start_date = Column(Date, nullable=True)
    planned_due_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="Pending")
    priority = Column(String(20), nullable=True)
    remarks = Column(String(1000), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(BIGINT, nullable=True)
    sequence_no = Column(BIGINT, nullable=True)
    dependency_task_id = Column(BIGINT, nullable=True)
    mandatory_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
