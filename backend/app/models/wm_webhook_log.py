from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmWebhookLog(Base):
    __tablename__ = "wm_webhook_log"

    log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    webhook_id = Column(BIGINT, nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)
    http_status_code = Column(BIGINT, nullable=True)
    error_message = Column(String(1000), nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
