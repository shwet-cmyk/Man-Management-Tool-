from pydantic import BaseModel, Field


class AlertSettingRequest(BaseModel):
    setting_code: str
    setting_name: str
    category: str
    entity_type: str
    trigger_type: str
    recipient_scope: str
    channel_type: str
    enabled_flag: bool = True
    period_type: str | None = None
    period_value: str | None = None
    template_id: int | None = None
    escalation_level: int = 0
    hide_downline_flag: bool = False
    applies_to_company_id: int | None = None
    applies_to_branch_id: int | None = None
    applies_to_department_id: int | None = None
    priority_filter: str | None = None
    active_flag: bool = True
    created_by: int = 1


class AlertTemplateRequest(BaseModel):
    template_code: str
    template_name: str
    category: str = "General"
    channel_type: str
    recipient_role_variant: str | None = None
    subject_template: str | None = None
    body_template: str
    enabled_flag: bool = True
    language_code: str = "en"
    version_no: int = 1
    created_by: int = 1


class AlertRecipientMatrixRequest(BaseModel):
    event_code: str
    entity_type: str
    recipient_role: str
    sequence_no: int = 1
    escalation_stage: int = 1
    include_flag: bool = True
    cc_flag: bool = False
    bcc_flag: bool = False
    suppression_rule_id: str | None = None
    hide_downline_flag: bool = False
    priority_filter: str | None = None
    active_flag: bool = True


class TriggerEventRequest(BaseModel):
    entity_type: str
    entity_id: int
    trigger_event: str
    payload: dict = {}
    triggered_by: int = 1


class ScheduledRunRequest(BaseModel):
    run_key: str = Field(default="daily", pattern="^(hourly|daily|weekly|monthly|manual)$")
    triggered_by: int = 1


class MarkReadRequest(BaseModel):
    alert_log_id: int
    user_id: int
