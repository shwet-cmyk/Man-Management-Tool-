from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmApiKey(Base):
    __tablename__ = "wm_api_key"

    api_key_id = Column(BIGINT, primary_key=True, autoincrement=True)
    client_name = Column(String(200), nullable=False)
    api_key = Column(String(500), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    rate_limit_per_minute = Column(BIGINT, nullable=False, default=1000)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
