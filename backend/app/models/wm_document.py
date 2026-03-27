from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String, Text

from app.database.session import Base


class WmDocument(Base):
    __tablename__ = "wm_document"

    document_id = Column(BIGINT, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    file_type = Column(String(100), nullable=False)
    file_tag = Column(String(100), nullable=True)
    file_hash = Column(String(128), nullable=True, index=True)
    uploaded_by = Column(BIGINT, nullable=False, index=True)
    version = Column(BIGINT, nullable=False, default=1)
    parent_document_id = Column(BIGINT, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
