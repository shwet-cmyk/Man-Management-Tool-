from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String

from app.database.session import Base


class WmGamificationEvent(Base):
    __tablename__ = "wm_gamification_event"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(BIGINT, nullable=False)
    event_code = Column(String(50), nullable=False)
    event_value = Column(String(200), nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
