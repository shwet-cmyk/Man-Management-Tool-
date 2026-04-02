from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class ReleaseNoteMaster(Base):
    __tablename__ = 'release_note_master'
    release_note_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    release_version: Mapped[str] = mapped_column(String(100), index=True)
    release_title: Mapped[str] = mapped_column(String(500))
    release_summary: Mapped[str] = mapped_column(Text)
    release_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    release_type: Mapped[str | None] = mapped_column(String(50))

