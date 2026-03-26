from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmExceptionHistory(Base):
    __tablename__ = "wm_exception_history"

    exception_history_id = Column(BIGINT, primary_key=True, autoincrement=True)
    exception_instance_id = Column(BIGINT, nullable=False, index=True)
    old_is_active = Column(Boolean, nullable=True)
    new_is_active = Column(Boolean, nullable=True)
    old_severity = Column(String(20), nullable=True)
    new_severity = Column(String(20), nullable=True)
    action_code = Column(String(30), nullable=False)
    action_note = Column(String(1000), nullable=True)
    acted_by = Column(BIGINT, nullable=True)
    acted_on = Column(DateTime, nullable=False, default=datetime.utcnow)
