from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UxPageSession(Base):
    __tablename__ = 'ux_page_session'
    page_session_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    session_id: Mapped[str] = mapped_column(String(100))
    route_path: Mapped[str] = mapped_column(String(300))
    screen_key: Mapped[str] = mapped_column(String(200), index=True)
    entered_at: Mapped[datetime] = mapped_column(DateTime)
    exited_at: Mapped[datetime | None] = mapped_column(DateTime)

