from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SearchQueryRequest(BaseModel):
    user_id: int
    query_text: str = Field(min_length=2, max_length=300)
    role: str


class SearchResult(BaseModel):
    search_index_id: int
    entity_type: str
    entity_id: str
    display_title: str
    display_subtitle: str | None = None
    route_path: str
    module_name: str


class SearchQueryResponse(BaseModel):
    query_text: str
    result_count: int
    groups: dict[str, list[SearchResult]]


class SearchIndexUpsert(BaseModel):
    entity_type: str
    entity_id: str
    display_title: str
    display_subtitle: str | None = None
    route_path: str
    module_name: str
    searchable_text: str
    privilege_code: str
    company_id: int | None = None
    branch_id: int | None = None
    department_id: int | None = None


class SettingUpsert(BaseModel):
    setting_key: str = Field(min_length=2, max_length=150)
    setting_label: str
    setting_value: str
    value_type: Literal['STRING', 'INT', 'FLOAT', 'BOOL', 'JSON']
    module_name: str
    settings_group_id: int
    scope_type: Literal['GLOBAL', 'COMPANY', 'BRANCH', 'DEPARTMENT', 'USER'] = 'GLOBAL'
    scope_reference_id: str | None = None
    is_editable: bool = True
    is_active: bool = True


class SettingResponse(SettingUpsert):
    setting_id: int


class ExceptionCreate(BaseModel):
    exception_type: str
    reference_module: str
    reference_id: str
    employee_user_id: int
    requested_by: int
    start_date: str
    end_date: str
    reason: str = Field(min_length=5)
    impact_type: str | None = None
    metadata_json: str | None = None


class ExceptionAction(BaseModel):
    actor_user_id: int
    action: Literal['APPROVE', 'REJECT']
    remarks: str | None = None


class FeatureFlagCreate(BaseModel):
    feature_code: str
    feature_name: str
    module_name: str
    description: str | None = None
    default_status: bool = False
    rollout_mode: Literal['GLOBAL', 'SCOPED', 'UAT_ONLY'] = 'GLOBAL'
    effective_from: str | None = None
    effective_to: str | None = None


class FeatureScopeUpsert(BaseModel):
    scope_type: Literal['ROLE', 'COMPANY', 'BRANCH', 'DEPARTMENT', 'USER', 'ENVIRONMENT']
    scope_reference_id: str
    is_enabled: bool


class MonitoringPolicyCreate(BaseModel):
    policy_name: str
    policy_type: str
    is_active: bool = True


class MonitoringPolicyVersionCreate(BaseModel):
    policy_master_id: int
    version_no: str
    policy_text: str = Field(min_length=5)
    effective_from: str


class PolicyAcceptanceCreate(BaseModel):
    policy_version_id: int
    user_id: int
    device_id: int | None = None
    acceptance_mode: Literal['WEB', 'AGENT', 'MOBILE'] = 'WEB'
    ip_address: str | None = None


class ImportJobCreate(BaseModel):
    import_type: Literal['USERS', 'TASK_MASTER', 'PROJECTS', 'ORG_STRUCTURE', 'TICKETS', 'TASKS']
    file_name: str
    uploaded_by: int
    rows: list[dict] = Field(default_factory=list)


class WebhookSubscriptionCreate(BaseModel):
    event_code: str
    endpoint_url: HttpUrl
    auth_type: Literal['NONE', 'BASIC', 'BEARER', 'HMAC'] = 'NONE'
    auth_config_json: str | None = None
    retry_policy_json: str | None = None


class ApiKeyCreate(BaseModel):
    key_name: str
    owner_user_id: int
    scope_json: str
    expires_at: str | None = None


class ImpersonationStart(BaseModel):
    admin_user_id: int
    target_user_id: int
    reason: str = Field(min_length=5)


class ArchivalPolicyUpsert(BaseModel):
    entity_name: str
    hot_retention_days: int = Field(gt=0)
    warm_retention_days: int = Field(gt=0)
    archive_retention_type: Literal['INDEFINITE', 'YEARS_1', 'YEARS_3', 'YEARS_7'] = 'INDEFINITE'
    purge_allowed: bool = False
    is_active: bool = True

    @field_validator('warm_retention_days')
    @classmethod
    def warm_not_less_than_hot(cls, value: int, info):
        hot = info.data.get('hot_retention_days')
        if hot is not None and value < hot:
            raise ValueError('warm_retention_days must be >= hot_retention_days')
        return value


class RestoreRequestCreate(BaseModel):
    entity_name: str
    record_reference: str
    reason: str = Field(min_length=5)
    created_by: int


class GenericReportResponse(BaseModel):
    generated_at: datetime
    rows: list[dict]
    total: int
