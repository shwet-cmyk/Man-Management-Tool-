from datetime import datetime

from sqlalchemy import BIGINT, DECIMAL, Boolean, Column, Date, DateTime, ForeignKey, String, Text

from app.database.session import Base


class WmGoal(Base):
    __tablename__ = "wm_goal"

    goal_id = Column(BIGINT, primary_key=True, autoincrement=True)
    goal_code = Column(String(50), nullable=False, unique=True, index=True)
    goal_name = Column(String(255), nullable=False)
    goal_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(BIGINT, nullable=False)
    owner_name = Column(String(255), nullable=False)
    team_id = Column(BIGINT, nullable=True)
    company_id = Column(BIGINT, nullable=False)
    branch_id = Column(BIGINT, nullable=True)
    department_id = Column(BIGINT, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="Draft")
    priority = Column(String(20), nullable=False, default="Medium")
    target_value = Column(DECIMAL(16, 2), nullable=True)
    current_value = Column(DECIMAL(16, 2), nullable=True)
    progress_percent = Column(DECIMAL(5, 2), nullable=False, default=0)
    measurement_type = Column(String(30), nullable=True)
    update_mode = Column(String(30), nullable=False, default="Manual")
    risk_status = Column(String(30), nullable=False, default="On Track")
    parent_goal_id = Column(BIGINT, ForeignKey("wm_goal.goal_id"), nullable=True)
    linked_project_count = Column(BIGINT, nullable=False, default=0)
    linked_task_count = Column(BIGINT, nullable=False, default=0)
    linked_metric_type = Column(String(50), nullable=True)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(BIGINT, nullable=True)
    updated_at = Column(DateTime, nullable=True)
