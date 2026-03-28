from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmTicketPauseHistory(Base):
    __tablename__ = "wm_ticket_pause_history"

    pause_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_id = Column(BIGINT, nullable=False, index=True)
    pause_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    pause_end = Column(DateTime, nullable=True)
    pause_reason = Column(String(120), nullable=False)
    paused_by = Column(BIGINT, nullable=False)
    total_minutes = Column(BIGINT, nullable=True)
    remarks = Column(Text, nullable=True)
