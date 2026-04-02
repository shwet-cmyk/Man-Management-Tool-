from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UrlClassificationMaster(Base):
    __tablename__ = 'url_classification_master'
    url_classification_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    domain_name: Mapped[str] = mapped_column(String(300))
    url_pattern: Mapped[str | None] = mapped_column(String(500))
    browser_scope: Mapped[str | None] = mapped_column(String(100))
    classification_type: Mapped[str] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

