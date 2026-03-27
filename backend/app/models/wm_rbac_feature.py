from sqlalchemy import BIGINT, Column, String

from app.database.session import Base


class WmRbacFeature(Base):
    __tablename__ = "wm_rbac_feature"

    feature_id = Column(BIGINT, primary_key=True, autoincrement=True)
    module_id = Column(BIGINT, nullable=False, index=True)
    name = Column(String(120), nullable=False, index=True)
