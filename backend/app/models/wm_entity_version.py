from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmEntityVersion(Base):
    __tablename__ = "wm_entity_version"

    entity_version_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(BIGINT, nullable=False, index=True)
    version_no = Column(BIGINT, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
