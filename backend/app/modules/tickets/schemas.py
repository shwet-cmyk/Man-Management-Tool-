from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    customer_id: int | None = None
    subject: str = Field(min_length=3, max_length=300)
    description: str
    priority: str = "MEDIUM"
    channel: str = "PORTAL"
    created_by: int
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    assigned_users: list[int] = Field(default_factory=list)
    auto_assign: bool = False


class TicketUpdateRequest(BaseModel):
    status: str | None = None
    priority: str | None = None
    subject: str | None = None
    description: str | None = None
    resolution_note: str | None = None
    changed_by: int


class TicketCommentRequest(BaseModel):
    user_id: int
    message: str
    is_internal: bool = False
    attachments: list[str] = Field(default_factory=list)


class TicketAssignRequest(BaseModel):
    user_ids: list[int]
    role: str = "OWNER"

