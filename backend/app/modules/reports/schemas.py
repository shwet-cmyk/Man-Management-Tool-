from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ReportDataSource = Literal["JOB", "EMPLOYEE"]
AggregationFunction = Literal["sum", "avg", "min", "max", "count"]
Frequency = Literal["DAILY", "WEEKLY", "MONTHLY"]
ExportFormat = Literal["CSV", "EXCEL", "PDF"]


class CreateReportRequest(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    created_by: int
    is_public: bool = False


class SaveReportConfigRequest(BaseModel):
    report_id: int
    data_source: ReportDataSource
    columns: list[str]
    filters: dict = Field(default_factory=dict)
    group_by: list[str] = Field(default_factory=list)
    aggregation: dict[str, AggregationFunction] = Field(default_factory=dict)


class CreateScheduleRequest(BaseModel):
    report_id: int
    frequency: Frequency
    recipients: list[int]
    next_run: datetime
    export_format: ExportFormat = "CSV"


class RunReportRequest(BaseModel):
    report_id: int
    requested_by: int
    filters: dict = Field(default_factory=dict)
    page: int = 1
    page_size: int = 100


class ExportReportRequest(BaseModel):
    report_id: int
    requested_by: int
    filters: dict = Field(default_factory=dict)
    export_format: ExportFormat
