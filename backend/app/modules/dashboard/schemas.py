from datetime import date
from typing import Literal

from pydantic import BaseModel


class DashboardCreateRequest(BaseModel):
    name: str
    user_id: int = 1
    role_id: int | None = None
    is_default: bool = False


class DashboardCreateResponse(BaseModel):
    status: str
    dashboard_id: int
    message: str


class WidgetConfig(BaseModel):
    data_source: Literal["JOB", "TASK", "PARTICIPANT", "TIMESHEET", "EXPENSE", "BILLING", "EXCEPTION"]
    dimension: str | None = None
    measure: str
    aggregation: Literal["SUM", "COUNT", "AVG"]


class WidgetAddRequest(BaseModel):
    dashboard_id: int
    widget_type: Literal["KPI", "CHART", "TABLE"]
    title: str
    position_x: int = 0
    position_y: int = 0
    width: int = 4
    height: int = 3
    config: WidgetConfig


class WidgetAddResponse(BaseModel):
    status: str
    widget_id: int
    message: str


class WidgetDataRequest(BaseModel):
    widget_id: int
    filters: dict = {}


class WidgetDataResponse(BaseModel):
    status: str
    widget_id: int
    data: list[dict]


class DashboardReadResponse(BaseModel):
    dashboard_id: int
    name: str
    user_id: int
    role_id: int | None
    is_default: bool
    widgets: list[dict]


class DashboardFilter(BaseModel):
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    customer_id: int | None = None
    manager_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
