from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class AgentRegistration(Base):
    __tablename__ = 'agent_registration'
    registration_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    registration_token: Mapped[str] = mapped_column(String(500))
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    agent_status: Mapped[str] = mapped_column(String(30), default='ACTIVE')
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

