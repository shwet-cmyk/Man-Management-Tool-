from sqlalchemy import BIGINT, Boolean, Column, Date, ForeignKey, String

from app.database.session import Base


class WmHolidayCalendar(Base):
    __tablename__ = "wm_holiday_calendar"

    holiday_calendar_id = Column(BIGINT, primary_key=True, autoincrement=True)
    calendar_name = Column(String(100), nullable=False)
    holiday_date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    weekly_off = Column(Boolean, nullable=False, default=False)
    shift_id = Column(BIGINT, ForeignKey("wm_shift_master.shift_id"), nullable=True)
