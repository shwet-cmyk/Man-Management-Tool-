from sqlalchemy import BIGINT, Boolean, Column, Integer, String

from app.database.session import Base


class WmRbacPermissionNode(Base):
    __tablename__ = "wm_rbac_permission_node"

    node_id = Column(BIGINT, primary_key=True, autoincrement=True)
    module_code = Column(String(80), nullable=False, index=True)
    permission_code = Column(String(120), nullable=False, unique=True, index=True)
    permission_label = Column(String(200), nullable=False)
    parent_permission_code = Column(String(120), nullable=True, index=True)
    permission_type = Column(String(40), nullable=False, default="VIEW")
    display_sequence = Column(Integer, nullable=False, default=1)
    is_module_flag = Column(Boolean, nullable=False, default=False)
    is_action_flag = Column(Boolean, nullable=False, default=True)
    is_sensitive_flag = Column(Boolean, nullable=False, default=False)
    active_flag = Column(Boolean, nullable=False, default=True)
