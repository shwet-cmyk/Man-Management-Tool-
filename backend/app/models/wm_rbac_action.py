from sqlalchemy import BIGINT, Column, String

from app.database.session import Base


class WmRbacAction(Base):
    __tablename__ = "wm_rbac_action"

    action_id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(40), nullable=False, unique=True, index=True)
