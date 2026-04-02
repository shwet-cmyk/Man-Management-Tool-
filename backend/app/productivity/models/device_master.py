from __future__ import annotations
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, Boolean, DECIMAL, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class DeviceMaster(Base):
    __tablename__ = 'device_master'
    device_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_uuid: Mapped[str] = mapped_column(String(200), unique=True)
    device_name: Mapped[str] = mapped_column(String(200))
    device_type: Mapped[str | None] = mapped_column(String(100))
    os_name: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(100))
    employee_user_id: Mapped[int] = mapped_column(BigInteger)
    company_id: Mapped[int] = mapped_column(BigInteger)
    branch_id: Mapped[int | None] = mapped_column(BigInteger)
    department_id: Mapped[int | None] = mapped_column(BigInteger)
    agent_version: Mapped[str | None] = mapped_column(String(50))
    registration_status: Mapped[str] = mapped_column(String(30), default='ACTIVE')
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

