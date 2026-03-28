from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmDocumentLink(Base):
    __tablename__ = "wm_document_link"

    document_link_id = Column(BIGINT, primary_key=True, autoincrement=True)
    document_id = Column(BIGINT, nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(BIGINT, nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
