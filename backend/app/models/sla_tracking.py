from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String

from app.database.session import Base


class SlaTracking(Base):
    __tablename__ = "sla_tracking"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), nullable=False, index=True)
    priority = Column(String(10), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    escalation_level = Column(Integer, nullable=False, default=0)
    paused = Column(Integer, nullable=False, default=0)
    pause_reason = Column(String(50), nullable=True)
    timezone = Column(String(40), nullable=False, default="UTC")
