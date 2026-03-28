from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmTaskParticipantDependency(Base):
    __tablename__ = "wm_task_participant_dependency"

    task_participant_dependency_id = Column(BIGINT, primary_key=True, autoincrement=True)
    task_id = Column(BIGINT, ForeignKey("wm_task.task_id"), nullable=False, index=True)
    predecessor_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=False)
    successor_participant_id = Column(BIGINT, ForeignKey("wm_task_participant.task_participant_id"), nullable=False)
    dependency_type = Column(String(30), nullable=False)
    lag_hours = Column(DECIMAL(10, 2), nullable=True)
    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
