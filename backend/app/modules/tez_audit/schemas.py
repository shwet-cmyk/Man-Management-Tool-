from pydantic import BaseModel, Field


class TezAuditLogRequest(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    user_id: str
    old_data: dict = Field(default_factory=dict)
    new_data: dict = Field(default_factory=dict)
    ip_address: str | None = None
    authorized: bool = True


class TezAuditReadResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    user_id: str
    created_at: str
