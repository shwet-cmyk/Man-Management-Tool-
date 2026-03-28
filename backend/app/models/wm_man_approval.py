from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmManApproval(Base):
    __tablename__ = "wm_man_approval"

    approval_id = Column(BIGINT, primary_key=True, autoincrement=True)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(BIGINT, nullable=False, index=True)
    approval_type = Column(String(40), nullable=False)
    current_status = Column(String(20), nullable=False, default="Pending")
    requested_by = Column(BIGINT, nullable=False)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_by = Column(BIGINT, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(BIGINT, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    remarks = Column(String(1000), nullable=True)
