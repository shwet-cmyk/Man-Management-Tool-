from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    external_ticket_no: str | None = None
    created_by: int
    customer_id: int | None = None
    customer_name: str | None = None
    product: str | None = None
    license_name_or_package: str | None = None
    remark: str | None = None
    category: str | None = None
    status: str = "Open"
    type: str = "Support"
    priority: str = "Medium"
    assign_executive_id: int | None = None
    assign_executive_name: str | None = None
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    mobile: str | None = None
    contact_person: str | None = None
    email: str | None = None
    address: str | None = None
    pack_validity: str | None = None
    sms_balance: int | None = None
    whatsapp_balance: int | None = None
    username: str | None = None
    max_user: int | None = None
    attachments: list[str] = Field(default_factory=list)
    subject: str = Field(min_length=3, max_length=300)
    description: str
    channel: str = "PORTAL"


class TicketUpdateRequest(BaseModel):
    status: str | None = None
    priority: str | None = None
    subject: str | None = None
    description: str | None = None
    resolution_note: str | None = None
    remark: str | None = None
    pause_reason: str | None = None
    changed_by: int


class TicketCommentRequest(BaseModel):
    user_id: int
    message: str
    is_internal: bool = False
    attachments: list[str] = Field(default_factory=list)


class TicketAssignRequest(BaseModel):
    user_ids: list[int]
    role: str = "OWNER"


class TicketFollowupRequest(BaseModel):
    action_type: str
    previous_status: str | None = None
    new_status: str | None = None
    note: str
    created_by: int
    is_customer_visible: bool = True
    attachment_refs: list[str] = Field(default_factory=list)


class TicketPauseRequest(BaseModel):
    paused: bool
    reason: str
    changed_by: int


class TicketConvertToTaskRequest(BaseModel):
    created_by: int
    override_priority: str | None = None


class TaskRolloverRequest(BaseModel):
    task_id: int
    previous_due_at: str
    revised_due_at: str
    changed_by: int
    reason: str
    remarks: str | None = None


class EscalationDigestRequest(BaseModel):
    run_at: str | None = None


class TicketDashboardRequest(BaseModel):
    stale_window_minutes: int = 24 * 60
