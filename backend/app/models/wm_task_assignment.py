from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.session import Base


class WmTaskAssignment(Base):
    __tablename__ = "wm_task_assignment"
    __table_args__ = (
        UniqueConstraint("task_id", "emp_id", "role_code", name="uq_task_assignment_unique"),
    )

    task_assignment_id = Column(BIGINT, primary_key=True, autoincrement=True)
    task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=False)
    emp_id = Column(BIGINT, nullable=False)
    role_code = Column(String(20), nullable=False)
    allocation_pct = Column(DECIMAL(5, 2), nullable=True)
    assigned_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    assigned_by = Column(BIGINT, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    task = relationship("WmTask", back_populates="assignments")
