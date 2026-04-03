from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class ReleaseNoteModuleMap(Base):
    __tablename__ = 'release_note_module_map'
    release_note_module_map_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    release_note_id: Mapped[int] = mapped_column(BigInteger)
    module_name: Mapped[str] = mapped_column(String(100))
    screen_key: Mapped[str | None] = mapped_column(String(200))
    route_path: Mapped[str | None] = mapped_column(String(300))

