from sqlalchemy import BIGINT, Column

from app.database.session import Base


class WmRbacPermissionScope(Base):
    __tablename__ = "wm_rbac_permission_scope"

    scope_id = Column(BIGINT, primary_key=True, autoincrement=True)
    permission_id = Column(BIGINT, nullable=False, index=True)
    company_id = Column(BIGINT, nullable=True)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
