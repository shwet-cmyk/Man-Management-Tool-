from datetime import datetime

from pydantic import BaseModel, Field


class TicketFetchRequest(BaseModel):
    mode: str = Field(default="full", pattern="^(full|incremental|filtered|manual)$")
    updated_after: datetime | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    ticket_no: str | None = None
    status: str | None = None
    priority: str | None = None
    open_only: bool = False
    limit: int = 100
    use_mock: bool | None = None
    triggered_by: int = 1


class TaskFromTicketRequest(BaseModel):
    ticket_no: str
    allow_duplicate: bool = False
    create_first_job: bool = False
    use_live_fetch: bool = False
    triggered_by: int = 1


class IntegrationConfigRequest(BaseModel):
    mock_mode: bool = True
    duplicate_policy: str = Field(default="block", pattern="^(block|allow|allow_if_closed)$")
    default_billable_flag: bool = False
    auto_create_first_job: bool = False
    default_primary_owner_emp_id: int | None = None
    default_manager_emp_id: int | None = None
    source_system_name: str = "TEZ_ERP"
