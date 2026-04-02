from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class ProductivityPolicyUpsertRequest(BaseModel):
    policy_name: str
    scope_type: str
    scope_reference_id: int | None = None
    idle_threshold_minutes: int
    productive_target_hours: float
    borderline_lower_hours: float
    underproductive_lower_hours: float
    screenshot_capture_enabled: bool = False
    screenshot_frequency_minutes: int | None = None
    raw_retention_days: int = 90
    screenshot_retention_days: int = 90
    warn_on_blacklisted_url: bool = True
    block_blacklisted_url: bool = False

class ProductivityPolicyResponse(BaseModel):
    policy_id: int
    policy_name: str
    scope_type: str
    scope_reference_id: int | None
    idle_threshold_minutes: int
    productive_target_hours: float
    borderline_lower_hours: float
    underproductive_lower_hours: float
    warn_on_blacklisted_url: bool
    block_blacklisted_url: bool
    effective_from: datetime
