from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmProjectFileLink(Base):
    __tablename__ = "wm_project_file_link"

    file_id = Column(BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BIGINT, ForeignKey("wm_project.project_id"), nullable=False, index=True)
    linked_entity_type = Column(String(20), nullable=False)
    linked_entity_id = Column(BIGINT, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size = Column(BIGINT, nullable=True)
    uploaded_by = Column(BIGINT, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    visibility_scope = Column(String(40), nullable=False, default="project_team_only")
