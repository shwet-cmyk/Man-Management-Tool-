from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, DECIMAL, Integer, String, Text

from app.database.session import Base


class WmIncrementConfig(Base):
    __tablename__ = "wm_increment_config"

    config_id = Column(BIGINT, primary_key=True, autoincrement=True)
    max_increment_percent = Column(DECIMAL(5, 2), nullable=False, default=12)
    scoring_period = Column(String(20), nullable=False, default="YEAR")
    point_to_increment_mode = Column(String(20), nullable=False, default="BAND")
    divisor_value = Column(DECIMAL(10, 2), nullable=True)
    score_bands_json = Column(Text, nullable=True)
    minimum_score_floor = Column(Integer, nullable=False, default=0)
    penalty_carry_forward_flag = Column(Boolean, nullable=False, default=True)
    manual_override_allowed_flag = Column(Boolean, nullable=False, default=False)
    manager_review_required_flag = Column(Boolean, nullable=False, default=True)
    active_flag = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
