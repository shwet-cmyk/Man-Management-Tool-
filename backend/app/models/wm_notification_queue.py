from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String, Text

from app.database.session import Base


class WmNotificationQueue(Base):
    __tablename__ = "wm_notification_queue"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(BIGINT, nullable=False)
    recipient_emp_id = Column(BIGINT, nullable=False)
    channel = Column(String(20), nullable=False, default="IN_APP")
    status = Column(String(20), nullable=False, default="PENDING")
    payload = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
