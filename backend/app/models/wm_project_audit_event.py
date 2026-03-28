from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, String, Text

from app.database.session import Base


class WmProjectAuditEvent(Base):
    __tablename__ = "wm_project_audit_event"

    project_audit_event_id = Column(BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BIGINT, ForeignKey("wm_project.project_id"), nullable=False, index=True)
    event_type = Column(String(60), nullable=False)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(BIGINT, nullable=True)
    actor_user_id = Column(BIGINT, nullable=False)
    actor_name = Column(String(255), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
