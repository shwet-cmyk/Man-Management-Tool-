from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmTicketTaskLink(Base):
    __tablename__ = "wm_ticket_task_link"

    ticket_task_link_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_id = Column(BIGINT, nullable=False, index=True)
    task_id = Column(BIGINT, nullable=False, index=True)
    source = Column(String(20), nullable=False, default="TICKET")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
