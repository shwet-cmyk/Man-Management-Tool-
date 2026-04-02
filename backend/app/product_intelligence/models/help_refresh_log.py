from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class HelpRefreshLog(Base):
    __tablename__ = 'help_refresh_log'
    help_refresh_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    screen_key: Mapped[str] = mapped_column(String(200), index=True)
    route_path: Mapped[str | None] = mapped_column(String(300), index=True)
    module_name: Mapped[str] = mapped_column(String(100))
    refresh_mode: Mapped[str] = mapped_column(String(30))
    refresh_status: Mapped[str] = mapped_column(String(30))
    triggered_by_release_version: Mapped[str | None] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

