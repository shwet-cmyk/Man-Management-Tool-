from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmTicket(Base):
    __tablename__ = "wm_ticket"

    ticket_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ticket_no = Column(String(50), nullable=False, unique=True, index=True)
    customer_id = Column(BIGINT, nullable=True, index=True)
    subject = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="MEDIUM")
    status = Column(String(30), nullable=False, default="NEW")
    channel = Column(String(30), nullable=False, default="PORTAL")
    created_by = Column(BIGINT, nullable=False)
    company_id = Column(BIGINT, nullable=True)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_on = Column(DateTime, nullable=True)
