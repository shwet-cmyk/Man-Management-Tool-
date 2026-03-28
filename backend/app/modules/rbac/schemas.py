from pydantic import BaseModel, Field


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    is_system_role: bool = False


class RoleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class PermissionAssignRequest(BaseModel):
    feature_name: str
    action_name: str
    module_name: str
    is_allowed: bool = True


class UserAssignRoleRequest(BaseModel):
    user_id: int | None = None
    role_id: int


class PermissionScopeRequest(BaseModel):
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None


class AccessCheckRequest(BaseModel):
    user_id: int
    module_name: str
    feature_name: str
    action_name: str
    entity_id: int | None = None
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    creator_user_id: int | None = None
    assignee_user_id: int | None = None
    manager_user_id: int | None = None


class ApprovalLimitRequest(BaseModel):
    module_name: str
    max_amount: float


class ApprovalCheckRequest(BaseModel):
    user_id: int
    module_name: str
    amount: float


class UserAccessProfileRequest(BaseModel):
    linked_employee_id: int | None = None
    linked_account_head_id: int | None = None
    approval_required_flag: bool = False
    access_type: str = "ANYWHERE"
    two_factor_email_flag: bool = False
    sms_flag: bool = False
    max_discount: float | None = None
    backdated_entries_access: str = "NONE"
    backdated_days_limit: int | None = None
    agent_level: str = "SELF_ONLY"
    entries_of_all: bool = False
    entries_of_self_only: bool = True
    entries_of_self_and_downline: bool = False
    active_flag: bool = True


class UserScopeMapRequest(BaseModel):
    scope_type: str
    scope_ids: list[int]


class EffectiveAccessRequest(BaseModel):
    user_id: int
    module_code: str
    permission_code: str
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None
    creator_user_id: int | None = None
    assignee_user_id: int | None = None
    manager_user_id: int | None = None
