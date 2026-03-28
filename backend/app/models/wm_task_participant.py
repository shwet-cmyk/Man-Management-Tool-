from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class WmTaskParticipant(Base):
    __tablename__ = "wm_task_participant"

    task_participant_id = Column(BIGINT, primary_key=True, autoincrement=True)
    task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=False, index=True)
    emp_id = Column(BIGINT, nullable=False)
    role_code = Column(String(30), nullable=False)
    planned_start = Column(DateTime, nullable=False)
    planned_due = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_due = Column(DateTime, nullable=True)
    sequence_no = Column(Integer, nullable=True)
    submission_required = Column(Boolean, nullable=False, default=False)
    acceptance_required = Column(Boolean, nullable=False, default=False)
    allocation_pct = Column(DECIMAL(5, 2), nullable=True)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    participant_status = Column(String(30), nullable=False, default="Planned")
    remarks = Column(Text, nullable=True)
    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    task = relationship("WmTask", back_populates="participants")
