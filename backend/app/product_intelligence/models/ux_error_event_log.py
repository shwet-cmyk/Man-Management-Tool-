from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UxErrorEventLog(Base):
    __tablename__ = 'ux_error_event_log'
    ux_error_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    screen_key: Mapped[str] = mapped_column(String(200), index=True)
    module_name: Mapped[str] = mapped_column(String(100))
    error_type: Mapped[str] = mapped_column(String(100))
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)

