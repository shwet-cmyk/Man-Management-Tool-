from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Text

from app.database.session import Base


class AuditLogV2(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(60), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(40), nullable=False)
    old_data = Column(Text, nullable=True)
    new_data = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=False)
    ip_address = Column(String(64), nullable=True)
    attempt_status = Column(String(20), nullable=False, default="AUTHORIZED")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
