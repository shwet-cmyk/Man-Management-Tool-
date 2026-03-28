from datetime import date

from pydantic import BaseModel


class ScoreTaskRequest(BaseModel):
    parent_task_id: int
    created_by: int = 1


class CapacityRequest(BaseModel):
    employee_id: int
    start_date: date
    end_date: date


class EmployeeSummaryRequest(BaseModel):
    employee_id: int
    start_date: date | None = None
    end_date: date | None = None


class EmployeeCalendarRequest(BaseModel):
    employee_id: int
    reference_date: date


class TeamCalendarRequest(BaseModel):
    manager_id: int
    start_date: date
    end_date: date


class CalendarDrilldownRequest(BaseModel):
    employee_id: int
    reference_date: date
    mode: str = "month"


class CalendarFilterRequest(BaseModel):
    employee_id: int | None = None
    manager_id: int | None = None
    start_date: date
    end_date: date
