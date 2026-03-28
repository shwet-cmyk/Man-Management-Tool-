from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmRbacAccessLog(Base):
    __tablename__ = "wm_rbac_access_log"

    access_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, nullable=False, index=True)
    module_name = Column(String(100), nullable=False, index=True)
    feature_name = Column(String(100), nullable=False)
    action_name = Column(String(100), nullable=False)
    entity_id = Column(BIGINT, nullable=True, index=True)
    is_allowed = Column(Boolean, nullable=False)
    reason = Column(String(200), nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
