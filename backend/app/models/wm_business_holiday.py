from sqlalchemy import BIGINT, Column, Date, String

from app.database.session import Base


class WmBusinessHoliday(Base):
    __tablename__ = "wm_business_holiday"

    holiday_id = Column(BIGINT, primary_key=True, autoincrement=True)
    holiday_date = Column(Date, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    company_id = Column(BIGINT, nullable=True)
    branch_id = Column(BIGINT, nullable=True)
