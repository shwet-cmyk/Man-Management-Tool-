from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class FeatureChangeLog(Base):
    __tablename__ = 'feature_change_log'
    feature_change_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    release_version: Mapped[str] = mapped_column(String(100), index=True)
    module_name: Mapped[str] = mapped_column(String(100))
    screen_key: Mapped[str | None] = mapped_column(String(200), index=True)
    route_path: Mapped[str | None] = mapped_column(String(300), index=True)
    change_category: Mapped[str] = mapped_column(String(100))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

