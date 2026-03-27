from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String, Text

from app.database.session import Base


class WmApiLog(Base):
    __tablename__ = "wm_api_log"

    log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    api_key_id = Column(BIGINT, nullable=True, index=True)
    endpoint = Column(String(200), nullable=False)
    request = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
