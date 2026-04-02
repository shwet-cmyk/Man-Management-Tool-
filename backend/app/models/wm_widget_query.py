from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmWidgetQuery(Base):
    __tablename__ = "wm_widget_query"

    widget_query_id = Column(BIGINT, primary_key=True, autoincrement=True)
    widget_id = Column(BIGINT, nullable=False, index=True)
    data_source = Column(String(50), nullable=False)
    dimension_field = Column(String(100), nullable=True)
    measure_field = Column(String(100), nullable=False)
    aggregation = Column(String(20), nullable=False)
    filter_json = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
