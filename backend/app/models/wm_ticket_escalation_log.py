from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmTicketEscalationLog(Base):
    __tablename__ = "wm_ticket_escalation_log"

    escalation_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_id = Column(BIGINT, nullable=False, index=True)
    escalation_level = Column(BIGINT, nullable=False)
    trigger_key = Column(String(80), nullable=False)
    recipients = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
