from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmSlaEscalation(Base):
    __tablename__ = "wm_sla_escalation"

    sla_escalation_id = Column(BIGINT, primary_key=True, autoincrement=True)
    sla_instance_id = Column(BIGINT, nullable=False, index=True)
    escalation_level = Column(BIGINT, nullable=False)
    escalated_to = Column(BIGINT, nullable=False)
    channel = Column(String(30), nullable=False, default="IN_APP")
    escalated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
