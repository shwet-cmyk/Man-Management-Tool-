from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmReportSchedule(Base):
    __tablename__ = "wm_report_schedule"

    schedule_id = Column(BIGINT, primary_key=True, autoincrement=True)
    report_id = Column(BIGINT, nullable=False, index=True)
    frequency = Column(String(20), nullable=False)
    recipients = Column(Text, nullable=False)
    next_run = Column(DateTime, nullable=False)
    export_format = Column(String(20), nullable=False, default="CSV")
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
