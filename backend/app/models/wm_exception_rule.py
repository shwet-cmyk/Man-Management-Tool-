from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, String

from app.database.session import Base


class WmExceptionRule(Base):
    __tablename__ = "wm_exception_rule"

    exception_rule_id = Column(BIGINT, primary_key=True, autoincrement=True)
    exception_type = Column(String(50), nullable=False)
    threshold_value = Column(DECIMAL(14, 2), nullable=True)
    threshold_unit = Column(String(20), nullable=True)
    severity_low = Column(String(100), nullable=True)
    severity_medium = Column(String(100), nullable=True)
    severity_high = Column(String(100), nullable=True)
    severity_critical = Column(String(100), nullable=True)
    calendar_aware = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
