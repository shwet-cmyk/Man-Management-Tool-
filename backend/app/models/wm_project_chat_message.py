from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, ForeignKey, String, Text

from app.database.session import Base


class WmProjectChatMessage(Base):
    __tablename__ = "wm_project_chat_message"

    message_id = Column(BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BIGINT, ForeignKey("wm_project.project_id"), nullable=False, index=True)
    entity_type = Column(String(20), nullable=False, default="PROJECT")
    entity_id = Column(BIGINT, nullable=True)
    message_type = Column(String(30), nullable=False, default="discussion")
    message_text = Column(Text, nullable=False)
    sender_user_id = Column(BIGINT, nullable=False)
    sender_name = Column(String(255), nullable=False)
    reply_to_message_id = Column(BIGINT, nullable=True)
    attachment_refs = Column(Text, nullable=True)
    visibility_scope = Column(String(40), nullable=False, default="project_team_only")
    pinned_flag = Column(Boolean, nullable=False, default=False)
    system_generated_flag = Column(Boolean, nullable=False, default=False)
    edited_flag = Column(Boolean, nullable=False, default=False)
    deleted_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
