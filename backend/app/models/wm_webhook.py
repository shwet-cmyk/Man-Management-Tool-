from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmWebhook(Base):
    __tablename__ = "wm_webhook"

    webhook_id = Column(BIGINT, primary_key=True, autoincrement=True)
    event_name = Column(String(100), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
