from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, Integer, String, Text

from app.database.session import Base


class WmAlertTemplate(Base):
    __tablename__ = "wm_alert_template"

    template_id = Column(BIGINT, primary_key=True, autoincrement=True)
    template_code = Column(String(80), nullable=False, unique=True, index=True)
    template_name = Column(String(200), nullable=False)
    category = Column(String(80), nullable=False, default="General")
    channel_type = Column(String(40), nullable=False)
    recipient_role_variant = Column(String(80), nullable=True)
    subject_template = Column(String(300), nullable=True)
    body_template = Column(Text, nullable=False)
    enabled_flag = Column(Boolean, nullable=False, default=True)
    language_code = Column(String(10), nullable=False, default="en")
    version_no = Column(Integer, nullable=False, default=1)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
