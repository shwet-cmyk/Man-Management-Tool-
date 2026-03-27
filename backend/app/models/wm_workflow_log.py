from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmWorkflowLog(Base):
    __tablename__ = "wm_workflow_log"

    workflow_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    instance_id = Column(BIGINT, nullable=False, index=True)
    node_id = Column(BIGINT, nullable=True)
    action = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)
    remarks = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
