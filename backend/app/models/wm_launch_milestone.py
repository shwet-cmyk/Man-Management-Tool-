from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, Date, DateTime, ForeignKey, String

from app.database.session import Base


class WmLaunchMilestone(Base):
    __tablename__ = "wm_launch_milestone"

    launch_milestone_id = Column(BIGINT, primary_key=True, autoincrement=True)
    launch_id = Column(BIGINT, ForeignKey("wm_launch.launch_id"), nullable=False, index=True)
    phase_name = Column(String(60), nullable=False)
    milestone_name = Column(String(255), nullable=False)
    owner_id = Column(BIGINT, nullable=True)
    status = Column(String(30), nullable=False, default="Planned")
    due_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    dependency_health = Column(String(30), nullable=False, default="Healthy")
    active_flag = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
