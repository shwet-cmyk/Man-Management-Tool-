from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, Integer, String

from app.database.session import Base


class WmAlertRecipientMatrix(Base):
    __tablename__ = "wm_alert_recipient_matrix"

    matrix_id = Column(BIGINT, primary_key=True, autoincrement=True)
    event_code = Column(String(120), nullable=False, index=True)
    entity_type = Column(String(40), nullable=False, index=True)
    recipient_role = Column(String(80), nullable=False)
    sequence_no = Column(Integer, nullable=False, default=1)
    escalation_stage = Column(Integer, nullable=False, default=1)
    include_flag = Column(Boolean, nullable=False, default=True)
    cc_flag = Column(Boolean, nullable=False, default=False)
    bcc_flag = Column(Boolean, nullable=False, default=False)
    suppression_rule_id = Column(String(120), nullable=True)
    hide_downline_flag = Column(Boolean, nullable=False, default=False)
    priority_filter = Column(String(20), nullable=True)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
