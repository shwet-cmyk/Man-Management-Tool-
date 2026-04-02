from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class PolicyBreachLog(Base):
    __tablename__ = 'policy_breach_log'
    breach_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    device_id: Mapped[int] = mapped_column(BigInteger, index=True)
    breach_timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    breach_type: Mapped[str] = mapped_column(String(50))
    app_name: Mapped[str | None] = mapped_column(String(300))
    domain_name: Mapped[str | None] = mapped_column(String(500))

