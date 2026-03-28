from sqlalchemy import BIGINT, Column

from app.database.session import Base


class WmSlaRule(Base):
    __tablename__ = "wm_sla_rule"

    sla_rule_id = Column(BIGINT, primary_key=True, autoincrement=True)
    workflow_id = Column(BIGINT, nullable=False, index=True)
    time_limit_minutes = Column(BIGINT, nullable=False)
    escalation_user_id = Column(BIGINT, nullable=False)
