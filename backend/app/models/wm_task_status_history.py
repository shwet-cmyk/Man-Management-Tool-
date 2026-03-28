from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String

from app.database.session import Base


class WmTaskStatusHistory(Base):
    __tablename__ = "wm_task_status_history"

    status_history_id = Column(BIGINT, primary_key=True, autoincrement=True)
    task_id = Column(BIGINT, nullable=False)
    old_status_code = Column(String(30), nullable=False)
    new_status_code = Column(String(30), nullable=False)
    action_code = Column(String(30), nullable=True)
    remarks = Column(String(1000), nullable=True)
    changed_by = Column(BIGINT, nullable=False)
    changed_on = Column(DateTime, nullable=False, default=datetime.utcnow)
