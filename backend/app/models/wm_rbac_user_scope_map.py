from sqlalchemy import BIGINT, Column, String

from app.database.session import Base


class WmRbacUserScopeMap(Base):
    __tablename__ = "wm_rbac_user_scope_map"

    scope_map_id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, nullable=False, index=True)
    scope_type = Column(String(20), nullable=False)  # COMPANY/BRANCH/DEPARTMENT
    scope_id = Column(BIGINT, nullable=False, index=True)
