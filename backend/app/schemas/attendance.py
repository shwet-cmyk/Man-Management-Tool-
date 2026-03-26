from datetime import date

from pydantic import BaseModel


class AttendanceBase(BaseModel):
    employee_id: int
    work_date: date
    status: str
    remarks: str | None = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceRead(AttendanceBase):
    id: int

    class Config:
        from_attributes = True
