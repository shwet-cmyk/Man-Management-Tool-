from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmCrmFollowup(Base):
    __tablename__ = "wm_crm_followup"

    followup_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(30), nullable=False, index=True)
    entity_id = Column(BIGINT, nullable=False, index=True)
    next_followup_date = Column(DateTime, nullable=False, index=True)
    remarks = Column(Text, nullable=True)
    assigned_to = Column(BIGINT, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING")
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
