from pydantic import BaseModel, Field


class AuditLogCreateRequest(BaseModel):
    entity_type: str
    entity_id: int
    action: str
    performed_by: int
    ip_address: str | None = None
    device_info: str | None = None
    source: str = "APP"
    old_data: dict = Field(default_factory=dict)
    new_data: dict = Field(default_factory=dict)


class AuditQueryContext(BaseModel):
    user_id: int
    module_name: str = "AUDIT"
    feature_name: str = "AUDIT"
    action_name: str = "VIEW"
