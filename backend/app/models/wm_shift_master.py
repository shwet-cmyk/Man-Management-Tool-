from sqlalchemy import BIGINT, DECIMAL, Column, String, Time

from app.database.session import Base


class WmShiftMaster(Base):
    __tablename__ = "wm_shift_master"

    shift_id = Column(BIGINT, primary_key=True, autoincrement=True)
    shift_name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    total_working_hours = Column(DECIMAL(8, 2), nullable=False)
    break_hours = Column(DECIMAL(8, 2), nullable=True)
    weekly_off_pattern = Column(String(100), nullable=True)
