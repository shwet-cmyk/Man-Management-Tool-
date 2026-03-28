from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmSlaInstance(Base):
    __tablename__ = "wm_sla_instance"

    sla_instance_id = Column(BIGINT, primary_key=True, autoincrement=True)
    sla_policy_id = Column(BIGINT, nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(BIGINT, nullable=False, index=True)
    assignee_user_id = Column(BIGINT, nullable=True)
    status = Column(String(30), nullable=False, default="RUNNING")
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_time = Column(DateTime, nullable=False)
    breach_time = Column(DateTime, nullable=True)
    paused_on = Column(DateTime, nullable=True)
    total_pause_seconds = Column(BIGINT, nullable=False, default=0)
    timezone = Column(String(50), nullable=False, default="UTC")
    context_json = Column(Text, nullable=True)
