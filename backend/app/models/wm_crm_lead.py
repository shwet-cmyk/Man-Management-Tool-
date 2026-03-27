from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmCrmLead(Base):
    __tablename__ = "wm_crm_lead"

    lead_id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    source = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="LEAD")
    assigned_users_json = Column(Text, nullable=False, default="[]")
    estimated_value = Column(BIGINT, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
