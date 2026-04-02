from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class RawActivityLog(Base):
    __tablename__ = 'raw_activity_log'
    activity_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    active_app_name: Mapped[str | None] = mapped_column(String(300))
    active_domain: Mapped[str | None] = mapped_column(String(500))
    active_url: Mapped[str | None] = mapped_column(Text)
    classification_type: Mapped[str | None] = mapped_column(String(30))
    is_idle: Mapped[bool] = mapped_column(Boolean, default=False)

