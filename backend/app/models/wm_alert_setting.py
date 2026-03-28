from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, Integer, String

from app.database.session import Base


class WmAlertSetting(Base):
    __tablename__ = "wm_alert_setting"

    setting_id = Column(BIGINT, primary_key=True, autoincrement=True)
    setting_code = Column(String(80), nullable=False, unique=True, index=True)
    setting_name = Column(String(200), nullable=False)
    category = Column(String(80), nullable=False)
    entity_type = Column(String(40), nullable=False)
    trigger_type = Column(String(60), nullable=False)
    recipient_scope = Column(String(100), nullable=False)
    channel_type = Column(String(40), nullable=False)
    enabled_flag = Column(Boolean, nullable=False, default=True)
    period_type = Column(String(40), nullable=True)
    period_value = Column(String(80), nullable=True)
    template_id = Column(BIGINT, nullable=True)
    escalation_level = Column(Integer, nullable=False, default=0)
    hide_downline_flag = Column(Boolean, nullable=False, default=False)
    applies_to_company_id = Column(BIGINT, nullable=True)
    applies_to_branch_id = Column(BIGINT, nullable=True)
    applies_to_department_id = Column(BIGINT, nullable=True)
    priority_filter = Column(String(20), nullable=True)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
