from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, String

from app.database.session import Base


class WmExpenseClaimAttachment(Base):
    __tablename__ = "wm_expense_claim_attachment"

    claim_attachment_id = Column(BIGINT, primary_key=True, autoincrement=True)
    claim_id = Column(BIGINT, ForeignKey("wm_expense_claim.claim_id"), nullable=False, index=True)
    file_ref = Column(String(1000), nullable=False)
    file_name = Column(String(255), nullable=True)
    uploaded_by = Column(BIGINT, nullable=False)
    uploaded_on = Column(DateTime, nullable=False, default=datetime.utcnow)
