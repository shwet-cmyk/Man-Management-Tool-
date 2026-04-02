from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class ProductivityAuditLog(Base):
    __tablename__ = 'productivity_audit_log'
    audit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    action_type: Mapped[str] = mapped_column(String(100))
    target_entity: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[int | None] = mapped_column(BigInteger)
    field_name: Mapped[str | None] = mapped_column(String(200))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)
    action_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

