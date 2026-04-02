from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class PolicyBreachResponse(BaseModel):
    breach_id: int
    user_id: int
    device_id: int
    breach_timestamp: datetime
    breach_type: str
    app_name: str | None = None
    domain_name: str | None = None
    action_taken: str | None = None
