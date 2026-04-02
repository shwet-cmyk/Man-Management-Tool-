from sqlalchemy import BIGINT, Boolean, Column

from app.database.session import Base


class WmRbacUserPermissionOverride(Base):
    __tablename__ = "wm_rbac_user_permission_override"

    override_id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, nullable=False, index=True)
    permission_id = Column(BIGINT, nullable=False, index=True)
    is_allowed = Column(Boolean, nullable=False)
