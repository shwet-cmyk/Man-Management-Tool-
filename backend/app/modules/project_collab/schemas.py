from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


ProjectType = Literal["Client Project", "Internal Project", "Ticket-based Project", "Strategic Project", "Operational Project"]
ProjectStatus = Literal["Draft", "Active", "On Hold", "At Risk", "Completed", "Closed", "Cancelled", "Archived"]
VisibilityScope = Literal[
    "internal_team_only",
    "project_team_only",
    "managers_only",
    "finance_only",
    "client_visible",
    "creator_and_managers",
    "all_with_record_access",
]


class ProjectCreateRequest(BaseModel):
    project_code: str
    project_name: str
    project_type: ProjectType
    description: str | None = None
    client_id: int | None = None
    client_name: str | None = None
    billable_flag: bool = False
    status: ProjectStatus = "Draft"
    priority: str = "Medium"
    owner_id: int
    owner_name: str
    manager_id: int | None = None
    manager_name: str | None = None
    company_id: int
    branch_id: int | None = None
    department_id: int | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    budget_amount: float | None = None
    created_by: int = 1


class ProjectStatusUpdateRequest(BaseModel):
    status: ProjectStatus
    updated_by: int
    updated_by_name: str = "System"


class ProjectTeamMemberCreateRequest(BaseModel):
    employee_id: int
    employee_name: str
    role_type: str
    participation_type: str
    notification_preference: str = "all"
    visible_in_team_list_flag: bool = True
    added_by: int = 1


class ProjectTeamMemberUpdateRequest(BaseModel):
    role_type: str | None = None
    participation_type: str | None = None
    notification_preference: str | None = None
    active_flag: bool | None = None


class ProjectMessageCreateRequest(BaseModel):
    project_id: int
    entity_type: Literal["PROJECT", "TASK", "JOB", "APPROVAL"] = "PROJECT"
    entity_id: int | None = None
    linked_record_code: str | None = None
    message_type: str = "discussion"
    message_text: str
    sender_user_id: int
    sender_name: str
    reply_to_message_id: int | None = None
    attachment_refs: list[str] = Field(default_factory=list)
    visibility_scope: VisibilityScope = "project_team_only"
    system_generated_flag: bool = False


class ProjectFileLinkRequest(BaseModel):
    project_id: int
    linked_entity_type: Literal["PROJECT", "TASK", "JOB", "CHAT_MESSAGE", "TIMESHEET"]
    linked_entity_id: int
    file_name: str
    file_type: str | None = None
    file_size: int | None = None
    uploaded_by: int
    visibility_scope: VisibilityScope = "project_team_only"


class ProjectWatcherRequest(BaseModel):
    project_id: int
    entity_type: Literal["PROJECT", "TASK", "JOB"] = "PROJECT"
    entity_id: int | None = None
    employee_id: int
    muted_flag: bool = False
    auto_follow_flag: bool = False


class ProjectAccessRequest(BaseModel):
    project_id: int
    employee_id: int
    employee_role: str
    is_project_member: bool
    scope_mode: Literal["self", "downline", "all"] = "self"
    can_view_financials: bool = False


class ProjectListFilterRequest(BaseModel):
    status: str | None = None
    project_type: str | None = None
    owner_id: int | None = None
    manager_id: int | None = None
    billable_flag: bool | None = None


class ProjectReportRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class ScenarioSeedRequest(BaseModel):
    created_by: int = 1
