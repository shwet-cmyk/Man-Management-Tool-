from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, Date, DateTime, Integer, String

from app.database.session import Base


class WmPointsEvent(Base):
    __tablename__ = "wm_points_event"

    points_event_id = Column(BIGINT, primary_key=True, autoincrement=True)
    employee_id = Column(BIGINT, nullable=False, index=True)
    source_entity_type = Column(String(20), nullable=False)
    source_entity_id = Column(BIGINT, nullable=False, index=True)
    parent_task_id = Column(BIGINT, nullable=True, index=True)
    job_id = Column(BIGINT, nullable=True, index=True)
    event_type = Column(String(60), nullable=False)
    event_reason = Column(String(500), nullable=False)
    event_date = Column(Date, nullable=False)
    due_date_reference = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    points_awarded = Column(Integer, nullable=False)
    positive_or_negative_flag = Column(String(10), nullable=False)
    evaluation_mode = Column(String(40), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(BIGINT, nullable=False)
    remarks = Column(String(1000), nullable=True)
    immutable_flag = Column(Boolean, nullable=False, default=True)
