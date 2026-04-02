from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EmployeeSyncRequest(BaseModel):
    sync_mode: str = Field(default="FULL", pattern="^(FULL|INCREMENTAL)$")


class EmployeeSyncResult(BaseModel):
    status: str
    total_fetched: int
    inserted: int
    updated: int
    skipped: int
    failed: int


class RefEmployeeRead(BaseModel):
    emp_id: int
    employee_name: str
    company_id: int
    branch_id: int | None
    department_id: int | None
    monthly_ctc: Decimal
    hourly_cost: Decimal | None
    is_active: bool
    last_synced_at: datetime

    class Config:
        from_attributes = True


class EmployeeSyncSummary(BaseModel):
    total_employees: int
    active_employees: int
    last_sync_time: datetime | None


class SyncLogRead(BaseModel):
    id: int
    entity: str
    sync_mode: str
    status: str
    total_fetched: int
    inserted: int
    updated: int
    skipped: int
    failed: int
    error_details: str | None
    started_at: datetime
    completed_at: datetime

    class Config:
        from_attributes = True
