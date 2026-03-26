from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmCustomerLifecycle(Base):
    __tablename__ = "wm_customer_lifecycle"

    customer_lifecycle_id = Column(BIGINT, primary_key=True, autoincrement=True)
    customer_id = Column(BIGINT, nullable=False, index=True)
    stage = Column(String(30), nullable=False, default="NEW")
    last_activity_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    churn_risk_score = Column(BIGINT, nullable=False, default=0)
