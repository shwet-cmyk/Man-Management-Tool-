from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Numeric, String

from app.database.session import Base


class WmForecast(Base):
    __tablename__ = "wm_forecast"

    forecast_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(30), nullable=False, index=True)
    entity_id = Column(BIGINT, nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_value = Column(Numeric(18, 2), nullable=False)
    model_used = Column(String(50), nullable=False, default="LINEAR_TREND")
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
