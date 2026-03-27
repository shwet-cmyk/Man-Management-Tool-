from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, String

from app.database.session import Base


class WmCrmDeal(Base):
    __tablename__ = "wm_crm_deal"

    deal_id = Column(BIGINT, primary_key=True, autoincrement=True)
    opportunity_id = Column(BIGINT, nullable=False, index=True)
    negotiated_value = Column(BIGINT, nullable=False)
    status = Column(String(30), nullable=False, default="NEGOTIATION")
    customer_name = Column(String(200), nullable=True)
    invoice_voucher_no = Column(String(100), nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
