from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmAuditFieldChange(Base):
    __tablename__ = "wm_audit_field_change"

    audit_field_change_id = Column(BIGINT, primary_key=True, autoincrement=True)
    audit_log_id = Column(BIGINT, nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
