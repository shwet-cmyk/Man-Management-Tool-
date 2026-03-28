from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmGoalLink(Base):
    __tablename__ = "wm_goal_link"

    goal_link_id = Column(BIGINT, primary_key=True, autoincrement=True)
    goal_id = Column(BIGINT, ForeignKey("wm_goal.goal_id"), nullable=False, index=True)
    linked_entity_type = Column(String(30), nullable=False)
    linked_entity_id = Column(BIGINT, nullable=False)
    linked_metric_type = Column(String(50), nullable=True)
    created_by = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
