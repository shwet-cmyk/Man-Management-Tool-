from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Numeric

from app.database.session import Base


class WmCustomerScore(Base):
    __tablename__ = "wm_customer_score"

    customer_score_id = Column(BIGINT, primary_key=True, autoincrement=True)
    customer_id = Column(BIGINT, nullable=False, index=True)
    churn_score = Column(Numeric(6, 4), nullable=False)
    repeat_probability = Column(Numeric(6, 4), nullable=False)
    lifetime_value = Column(Numeric(18, 2), nullable=False)
    updated_on = Column(DateTime, nullable=False, default=datetime.utcnow)
