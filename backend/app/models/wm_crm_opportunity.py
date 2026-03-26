from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmCrmOpportunity(Base):
    __tablename__ = "wm_crm_opportunity"

    opportunity_id = Column(BIGINT, primary_key=True, autoincrement=True)
    lead_id = Column(BIGINT, nullable=False, index=True)
    value = Column(BIGINT, nullable=False)
    probability = Column(BIGINT, nullable=False, default=30)
    expected_close_date = Column(DateTime, nullable=True)
    status = Column(String(30), nullable=False, default="OPEN")
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
