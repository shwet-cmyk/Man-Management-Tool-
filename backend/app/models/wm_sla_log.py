from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmSlaLog(Base):
    __tablename__ = "wm_sla_log"

    sla_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    instance_id = Column(BIGINT, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    breach_time = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False, default="RUNNING")
    paused_on = Column(DateTime, nullable=True)
    total_pause_seconds = Column(BIGINT, nullable=False, default=0)
