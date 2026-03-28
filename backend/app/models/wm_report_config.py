from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmReportConfig(Base):
    __tablename__ = "wm_report_config"

    config_id = Column(BIGINT, primary_key=True, autoincrement=True)
    report_id = Column(BIGINT, nullable=False, index=True)
    data_source = Column(String(50), nullable=False)
    columns_json = Column(Text, nullable=False)
    filters_json = Column(Text, nullable=True)
    group_by = Column(String(250), nullable=True)
    aggregation = Column(String(250), nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
