from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.session import Base


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),)

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    work_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # Present, Absent, Leave, WFH
    remarks = Column(String(255), nullable=True)

    employee = relationship("Employee", back_populates="attendance_logs")
