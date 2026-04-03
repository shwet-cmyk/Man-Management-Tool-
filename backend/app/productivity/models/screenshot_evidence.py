from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class ScreenshotEvidence(Base):
    __tablename__ = 'screenshot_evidence'
    screenshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    device_id: Mapped[int] = mapped_column(BigInteger, index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime)
    trigger_type: Mapped[str] = mapped_column(String(50))
    storage_path: Mapped[str] = mapped_column(Text)

