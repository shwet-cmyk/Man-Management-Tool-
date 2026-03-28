from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmRule(Base):
    __tablename__ = "wm_rule"

    rule_id = Column(BIGINT, primary_key=True, autoincrement=True)
    module = Column(String(100), nullable=False, index=True)
    condition_json = Column(Text, nullable=False)
    action_json = Column(Text, nullable=False)
    priority = Column(BIGINT, nullable=False, default=100)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
