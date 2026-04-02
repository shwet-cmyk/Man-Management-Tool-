from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Column, DateTime, String

from app.database.session import Base


class WmAiPrediction(Base):
    __tablename__ = "wm_ai_prediction"

    prediction_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(BIGINT, nullable=False, index=True)
    prediction_type = Column(String(50), nullable=False)
    predicted_value = Column(DECIMAL(18, 2), nullable=False)
    probability = Column(DECIMAL(5, 2), nullable=False)
    model_version = Column(String(30), nullable=False, default="rule-v1")
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
