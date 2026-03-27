from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmTicketHistory(Base):
    __tablename__ = "wm_ticket_history"

    history_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_id = Column(BIGINT, nullable=False, index=True)
    field = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(BIGINT, nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
