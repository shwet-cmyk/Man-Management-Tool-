from sqlalchemy import BIGINT, Column, String

from app.database.session import Base


class WmRbacModule(Base):
    __tablename__ = "wm_rbac_module"

    module_id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
