from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, DateTime, Integer, String, Text

from app.database.session import Base


class WmTaskChildItem(Base):
    __tablename__ = "wm_task_child_item"

    child_item_id = Column(BIGINT, primary_key=True, autoincrement=True)
    parent_task_id = Column(BIGINT, nullable=False)
    item_type = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    assignee_emp_id = Column(BIGINT, nullable=True)
    due_at = Column(DateTime, nullable=True)
    priority_code = Column(String(20), nullable=True)
    estimated_hours = Column(DECIMAL(12, 2), nullable=True)
    status_code = Column(String(30), nullable=False, default="Open")
    sequence_no = Column(Integer, nullable=True)
    source_type = Column(String(20), nullable=False, default="MANUAL")
    created_by = Column(BIGINT, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_on = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
