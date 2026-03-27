from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime

from app.database.session import Base


class WmRbacUserRole(Base):
    __tablename__ = "wm_rbac_user_role"

    user_role_id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, nullable=False, index=True)
    role_id = Column(BIGINT, nullable=False, index=True)
    assigned_on = Column(DateTime, nullable=False, default=datetime.utcnow)
