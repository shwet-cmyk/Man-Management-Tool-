from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), nullable=False, unique=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    job_title = Column(String(100), nullable=False)
    join_date = Column(Date, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    department = relationship("Department", back_populates="employees")
    attendance_logs = relationship("Attendance", back_populates="employee")
