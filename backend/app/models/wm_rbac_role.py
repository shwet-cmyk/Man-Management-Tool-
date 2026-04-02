from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String, Text

from app.database.session import Base


class WmRbacRole(Base):
    __tablename__ = "wm_rbac_role"

    role_id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
