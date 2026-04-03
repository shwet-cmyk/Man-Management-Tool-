from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UxDeadClickLog(Base):
    __tablename__ = 'ux_dead_click_log'
    dead_click_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    screen_key: Mapped[str] = mapped_column(String(200), index=True)
    route_path: Mapped[str] = mapped_column(String(300))
    click_timestamp: Mapped[datetime] = mapped_column(DateTime)
    click_count: Mapped[int] = mapped_column(Integer, default=1)

