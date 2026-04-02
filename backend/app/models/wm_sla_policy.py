from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmSlaPolicy(Base):
    __tablename__ = "wm_sla_policy"

    sla_policy_id = Column(BIGINT, primary_key=True, autoincrement=True)
    module = Column(String(50), nullable=False, index=True)
    condition_json = Column(Text, nullable=True)
    response_time_minutes = Column(BIGINT, nullable=False)
    resolution_time_minutes = Column(BIGINT, nullable=False)
    escalation_config_json = Column(Text, nullable=False)
    company_id = Column(BIGINT, nullable=True)
    branch_id = Column(BIGINT, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
