from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmProjectWatcher(Base):
    __tablename__ = "wm_project_watcher"

    watcher_id = Column(BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BIGINT, ForeignKey("wm_project.project_id"), nullable=False, index=True)
    entity_type = Column(String(20), nullable=False, default="PROJECT")
    entity_id = Column(BIGINT, nullable=True)
    employee_id = Column(BIGINT, nullable=False, index=True)
    muted_flag = Column(Boolean, nullable=False, default=False)
    auto_follow_flag = Column(Boolean, nullable=False, default=False)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
