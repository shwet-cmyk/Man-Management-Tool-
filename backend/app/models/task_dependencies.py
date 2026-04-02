from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String

from app.database.session import Base


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    depends_on_user_id = Column(String(36), nullable=False, index=True)
    depends_on_task_id = Column(String(36), nullable=True, index=True)
    dependency_type = Column(String(2), nullable=False, default="FS")
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
