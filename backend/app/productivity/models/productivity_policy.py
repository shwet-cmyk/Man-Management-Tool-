from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class ProductivityPolicy(Base):
    __tablename__ = 'productivity_policy'
    policy_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    policy_name: Mapped[str] = mapped_column(String(200))
    scope_type: Mapped[str] = mapped_column(String(30))
    scope_reference_id: Mapped[int | None] = mapped_column(BigInteger)
    idle_threshold_minutes: Mapped[int] = mapped_column(Integer)
    productive_target_hours: Mapped[float] = mapped_column(DECIMAL(10,2))
    borderline_lower_hours: Mapped[float] = mapped_column(DECIMAL(10,2))
    underproductive_lower_hours: Mapped[float] = mapped_column(DECIMAL(10,2))
    screenshot_capture_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    screenshot_frequency_minutes: Mapped[int | None] = mapped_column(Integer)
    raw_retention_days: Mapped[int] = mapped_column(Integer, default=90)
    screenshot_retention_days: Mapped[int] = mapped_column(Integer, default=90)
    summary_retention_type: Mapped[str] = mapped_column(String(30), default='PERPETUAL')
    warn_on_blacklisted_url: Mapped[bool] = mapped_column(Boolean, default=True)
    block_blacklisted_url: Mapped[bool] = mapped_column(Boolean, default=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

