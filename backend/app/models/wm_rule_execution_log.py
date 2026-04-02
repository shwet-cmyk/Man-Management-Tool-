from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String, Text

from app.database.session import Base


class WmRuleExecutionLog(Base):
    __tablename__ = "wm_rule_execution_log"

    rule_execution_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    rule_id = Column(BIGINT, nullable=False, index=True)
    module = Column(String(100), nullable=False)
    matched = Column(String(5), nullable=False)
    context_json = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
