from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String

from app.database.session import Base


class WmTaskWorkflowState(Base):
    __tablename__ = "wm_task_workflow_state"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(BIGINT, nullable=False)
    workflow_id = Column(BIGINT, nullable=True)
    state_code = Column(String(30), nullable=False)
    entered_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    entered_by = Column(BIGINT, nullable=False)
