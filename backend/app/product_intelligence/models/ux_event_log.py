from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UxEventLog(Base):
    __tablename__ = 'ux_event_log'
    ux_event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    screen_key: Mapped[str] = mapped_column(String(200), index=True)
    route_path: Mapped[str] = mapped_column(String(300), index=True)
    module_name: Mapped[str] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(100))
    event_timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text)

