from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UxAiRecommendation(Base):
    __tablename__ = 'ux_ai_recommendation'
    recommendation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    module_name: Mapped[str] = mapped_column(String(100))
    screen_key: Mapped[str | None] = mapped_column(String(200))
    recommendation_title: Mapped[str] = mapped_column(String(500))
    recommendation_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

