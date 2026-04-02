from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String, Text

from app.database.session import Base


class WmDashboardWidget(Base):
    __tablename__ = "wm_dashboard_widget"

    widget_id = Column(BIGINT, primary_key=True, autoincrement=True)
    dashboard_id = Column(BIGINT, nullable=False, index=True)
    widget_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    position_x = Column(Integer, nullable=False, default=0)
    position_y = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=False, default=4)
    height = Column(Integer, nullable=False, default=3)
    config_json = Column(Text, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
