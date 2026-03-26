from datetime import datetime

from sqlalchemy import BIGINT, Column, DateTime, Numeric

from app.database.session import Base


class WmSalesHistory(Base):
    __tablename__ = "wm_sales_history"

    sales_history_id = Column(BIGINT, primary_key=True, autoincrement=True)
    sales_date = Column(DateTime, nullable=False, index=True)
    product_id = Column(BIGINT, nullable=False, index=True)
    customer_id = Column(BIGINT, nullable=False, index=True)
    quantity = Column(Numeric(18, 2), nullable=False)
    revenue = Column(Numeric(18, 2), nullable=False)
    branch_id = Column(BIGINT, nullable=False, index=True)
    created_on = Column(DateTime, nullable=False, default=datetime.utcnow)
