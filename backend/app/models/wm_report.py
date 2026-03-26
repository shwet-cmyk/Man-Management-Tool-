from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmReport(Base):
    __tablename__ = "wm_report"

    report_id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    created_by = Column(BIGINT, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
