from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, Text

from app.database.session import Base


class WmTicketComment(Base):
    __tablename__ = "wm_ticket_comment"

    comment_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_id = Column(BIGINT, nullable=False, index=True)
    user_id = Column(BIGINT, nullable=False)
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, nullable=False, default=False)
    attachments = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
