from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmDashboard(Base):
    __tablename__ = "wm_dashboard"

    dashboard_id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    user_id = Column(BIGINT, nullable=False, index=True)
    role_id = Column(BIGINT, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
