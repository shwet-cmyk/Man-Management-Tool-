from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmDocumentAudit(Base):
    __tablename__ = "wm_document_audit"

    document_audit_id = Column(BIGINT, primary_key=True, autoincrement=True)
    document_id = Column(BIGINT, nullable=False, index=True)
    action = Column(String(50), nullable=False)
    user_id = Column(BIGINT, nullable=False, index=True)
    remarks = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
