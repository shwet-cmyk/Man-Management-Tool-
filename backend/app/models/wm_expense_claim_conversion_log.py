from datetime import datetime

from sqlalchemy import BIGINT, Boolean, Column, DateTime, String, Text

from app.database.session import Base


class WmExpenseClaimConversionLog(Base):
    __tablename__ = "wm_expense_claim_conversion_log"

    claim_conversion_log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    claim_id = Column(BIGINT, nullable=False, index=True)
    old_conversion_status = Column(String(30), nullable=False)
    new_conversion_status = Column(String(30), nullable=False)
    voucher_id = Column(BIGINT, nullable=True)
    voucher_no = Column(String(100), nullable=True)
    request_payload = Column(Text, nullable=True)
    response_payload = Column(Text, nullable=True)
    conversion_error = Column(Text, nullable=True)
    converted_by = Column(BIGINT, nullable=False)
    converted_on = Column(DateTime, nullable=False, default=datetime.utcnow)
    override_flag = Column(Boolean, nullable=False, default=False)
    override_reason = Column(String(1000), nullable=True)
