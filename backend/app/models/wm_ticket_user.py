from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmTicketUser(Base):
    __tablename__ = "wm_ticket_user"

    ticket_user_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_id = Column(BIGINT, nullable=False, index=True)
    user_id = Column(BIGINT, nullable=False, index=True)
    role = Column(String(30), nullable=False, default="OWNER")
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
