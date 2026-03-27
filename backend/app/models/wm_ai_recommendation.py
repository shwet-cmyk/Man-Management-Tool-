from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, Integer, String, Text

from app.database.session import Base


class WmAiRecommendation(Base):
    __tablename__ = "wm_ai_recommendation"

    rec_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_id = Column(BIGINT, nullable=False, index=True)
    recommendation_type = Column(String(100), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    priority = Column(Integer, nullable=False, default=3)
    is_applied = Column(Boolean, nullable=False, default=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
