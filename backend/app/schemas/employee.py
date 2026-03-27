from datetime import date

from pydantic import BaseModel, EmailStr


class EmployeeBase(BaseModel):
    employee_code: str
    full_name: str
    email: EmailStr
    job_title: str
    join_date: date
    department_id: int


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeRead(EmployeeBase):
    id: int

    class Config:
        from_attributes = True
