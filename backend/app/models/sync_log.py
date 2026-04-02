from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.session import Base


class SyncLog(Base):
    __tablename__ = "sync_log"

    id = Column(Integer, primary_key=True, index=True)
    entity = Column(String(50), nullable=False)
    sync_mode = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    total_fetched = Column(Integer, nullable=False, default=0)
    inserted = Column(Integer, nullable=False, default=0)
    updated = Column(Integer, nullable=False, default=0)
    skipped = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    error_details = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
