from datetime import date

from pydantic import BaseModel, Field


class AnalyticsFilter(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    employee_id: int | None = None
    manager_id: int | None = None
    client_id: int | None = None
    product: str | None = None
    category: str | None = None
    priority: str | None = None
    status: str | None = None
    billable_flag: bool | None = None
    critical_flag: bool | None = None
    overdue_flag: bool | None = None
    approval_status: str | None = None
    billing_readiness: str | None = None
    source_type: str | None = None


class WidgetQueryRequest(BaseModel):
    widget_type: str = Field(pattern="^(summary_card|grouped_bar|stacked_bar|line_trend|donut|leaderboard|pivot|heatmap|comparison|progress|alert|ranked_grid)$")
    metric_code: str
    group_by: list[str] = []
    filters: AnalyticsFilter = AnalyticsFilter()
    top_n: int = 10


class TrendQueryRequest(BaseModel):
    metric_code: str
    grain: str = Field(default="month", pattern="^(day|week|month|quarter|year)$")
    filters: AnalyticsFilter = AnalyticsFilter()


class DrilldownRequest(BaseModel):
    entity_type: str = Field(pattern="^(ticket|task|job|timesheet|approval|client|employee)$")
    metric_code: str
    filters: AnalyticsFilter = AnalyticsFilter()
