from sqlalchemy import BIGINT, Column

from app.database.session import Base


class WmRbacRoleInheritance(Base):
    __tablename__ = "wm_rbac_role_inheritance"

    role_inheritance_id = Column(BIGINT, primary_key=True, autoincrement=True)
    parent_role_id = Column(BIGINT, nullable=False, index=True)
    child_role_id = Column(BIGINT, nullable=False, index=True)
