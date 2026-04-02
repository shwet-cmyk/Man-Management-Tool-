from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime

from app.database.session import Base


class WmRbacPermission(Base):
    __tablename__ = "wm_rbac_permission"

    permission_id = Column(BIGINT, primary_key=True, autoincrement=True)
    role_id = Column(BIGINT, nullable=False, index=True)
    feature_id = Column(BIGINT, nullable=False, index=True)
    action_id = Column(BIGINT, nullable=False, index=True)
    is_allowed = Column(Boolean, nullable=False, default=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
