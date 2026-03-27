from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String, Text

from app.database.session import Base


class TaskAuditLog(Base):
    __tablename__ = "wm_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    entity_name = Column(String(50), nullable=False)
    entity_id = Column(BIGINT, nullable=False)
    action = Column(String(30), nullable=False)
    details = Column(Text, nullable=True)
    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(String(64), nullable=True)
    device_info = Column(String(255), nullable=True)
    source = Column(String(30), nullable=True, default="APP")
