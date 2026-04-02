from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class MonthlyProductivitySummary(Base):
    __tablename__ = 'monthly_productivity_summary'
    monthly_summary_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    summary_month: Mapped[int] = mapped_column(Integer)
    summary_year: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    productive_minutes: Mapped[int] = mapped_column(Integer, default=0)
    idle_minutes: Mapped[int] = mapped_column(Integer, default=0)
    productivity_status: Mapped[str | None] = mapped_column(String(30))

