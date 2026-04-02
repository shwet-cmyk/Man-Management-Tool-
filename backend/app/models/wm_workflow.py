from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String

from app.database.session import Base


class WmWorkflow(Base):
    __tablename__ = "wm_workflow"

    workflow_id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    module = Column(String(100), nullable=False, index=True)
    trigger_event = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    version = Column(BIGINT, nullable=False, default=1)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
