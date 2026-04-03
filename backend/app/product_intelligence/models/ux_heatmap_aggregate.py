from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Date, DECIMAL, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UxHeatmapAggregate(Base):
    __tablename__ = 'ux_heatmap_aggregate'
    heatmap_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    screen_key: Mapped[str] = mapped_column(String(200), index=True)
    route_path: Mapped[str] = mapped_column(String(300), index=True)
    heatmap_type: Mapped[str] = mapped_column(String(50))
    aggregate_date: Mapped[datetime.date] = mapped_column(Date)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)

