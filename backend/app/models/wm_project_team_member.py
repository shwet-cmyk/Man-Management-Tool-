from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmProjectTeamMember(Base):
    __tablename__ = "wm_project_team_member"

    project_team_member_id = Column(BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BIGINT, ForeignKey("wm_project.project_id"), nullable=False, index=True)
    employee_id = Column(BIGINT, nullable=False, index=True)
    employee_name = Column(String(255), nullable=False)
    role_type = Column(String(50), nullable=False)
    participation_type = Column(String(50), nullable=False)
    notification_preference = Column(String(30), nullable=False, default="all")
    visible_in_team_list_flag = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    active_flag = Column(Boolean, nullable=False, default=True)
    added_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
