from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Integer, String

from app.database.session import Base


class WmTaskChildItemConversion(Base):
    __tablename__ = "wm_task_child_item_conversion"

    conversion_id = Column(BIGINT, primary_key=True, autoincrement=True)
    source_child_item_id = Column(BIGINT, nullable=False)
    target_task_id = Column(BIGINT, nullable=True)
    conversion_type = Column(String(30), nullable=False)
    converted_by = Column(BIGINT, nullable=False)
    converted_on = Column(DateTime, nullable=False, default=datetime.utcnow)
