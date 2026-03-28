from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String, Text

from app.database.session import Base


class WmTicketFollowup(Base):
    __tablename__ = "wm_ticket_followup"

    followup_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_id = Column(BIGINT, nullable=False, index=True)
    action_type = Column(String(30), nullable=False)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    note = Column(Text, nullable=False)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_customer_visible = Column(Boolean, nullable=False, default=True)
    attachment_refs = Column(Text, nullable=True)
