from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmWorkflowInstance(Base):
    __tablename__ = "wm_workflow_instance"

    instance_id = Column(BIGINT, primary_key=True, autoincrement=True)
    workflow_id = Column(BIGINT, nullable=False, index=True)
    workflow_version = Column(BIGINT, nullable=False, default=1)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(BIGINT, nullable=False, index=True)
    status = Column(String(30), nullable=False, default="RUNNING")
    context_json = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_on = Column(DateTime, nullable=True)
