from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String, Text

from app.database.session import Base


class WmAlertLog(Base):
    __tablename__ = "wm_alert_log"

    alert_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    setting_id = Column(BIGINT, nullable=False, index=True)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(BIGINT, nullable=False, index=True)
    trigger_event = Column(String(60), nullable=False)
    recipient_role = Column(String(80), nullable=True)
    recipient_user_id = Column(BIGINT, nullable=True, index=True)
    recipient_channel = Column(String(40), nullable=False)
    message_subject = Column(String(400), nullable=True)
    message_body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="Queued")
    sent_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(String(1000), nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
