from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmAttachment(Base):
    __tablename__ = "wm_attachment"

    attachment_id = Column(BIGINT, primary_key=True, autoincrement=True)
    linked_entity_type = Column(String(30), nullable=False)
    linked_entity_id = Column(BIGINT, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(30), nullable=False)
    file_size = Column(BIGINT, nullable=False)
    uploaded_by = Column(BIGINT, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
