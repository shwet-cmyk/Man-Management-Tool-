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


class ApprovalLimitRequest(BaseModel):
    module_name: str
    max_amount: float


class ApprovalCheckRequest(BaseModel):
    user_id: int
    module_name: str
    amount: float
