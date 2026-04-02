from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UnderproductiveFlagLog(Base):
    __tablename__ = 'underproductive_flag_log'
    flag_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    summary_date: Mapped[datetime.date] = mapped_column(Date, index=True)
    productive_minutes: Mapped[int] = mapped_column(Integer)
    target_minutes: Mapped[int] = mapped_column(Integer)
    productivity_status: Mapped[str] = mapped_column(String(30))

