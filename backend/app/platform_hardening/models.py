from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AuditMixin:
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GlobalSearchIndex(Base):
    __tablename__ = 'global_search_index'
    search_index_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(100))
    display_title: Mapped[str] = mapped_column(String(300))
    display_subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    route_path: Mapped[str] = mapped_column(String(300))
    module_name: Mapped[str] = mapped_column(String(100))
    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    department_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    searchable_text: Mapped[str] = mapped_column(Text)
    privilege_code: Mapped[str] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GlobalSearchLog(Base):
    __tablename__ = 'global_search_log'
    search_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    query_text: Mapped[str] = mapped_column(String(300))
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    clicked_result_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    searched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SettingsGroup(Base, AuditMixin):
    __tablename__ = 'settings_group'
    settings_group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SettingsRegistry(Base, AuditMixin):
    __tablename__ = 'settings_registry'
    setting_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    settings_group_id: Mapped[int] = mapped_column(Integer)
    setting_key: Mapped[str] = mapped_column(String(150), unique=True)
    setting_label: Mapped[str] = mapped_column(String(300))
    setting_value: Mapped[str] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(String(30))
    module_name: Mapped[str] = mapped_column(String(100))
    scope_type: Mapped[str] = mapped_column(String(30), default='GLOBAL')
    scope_reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SettingsChangeLog(Base):
    __tablename__ = 'settings_change_log'
    settings_change_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    setting_id: Mapped[int] = mapped_column(Integer)
    changed_by: Mapped[int] = mapped_column(Integer)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExceptionRegister(Base, AuditMixin):
    __tablename__ = 'exception_register'
    exception_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exception_type: Mapped[str] = mapped_column(String(100))
    reference_module: Mapped[str] = mapped_column(String(100))
    reference_id: Mapped[str] = mapped_column(String(100))
    employee_user_id: Mapped[int] = mapped_column(Integer)
    requested_by: Mapped[int] = mapped_column(Integer)
    approved_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[str] = mapped_column(String(30))
    end_date: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='PENDING')
    impact_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExceptionApprovalLog(Base):
    __tablename__ = 'exception_approval_log'
    exception_approval_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exception_id: Mapped[int] = mapped_column(Integer)
    actor_user_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(30))
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FeatureFlagMaster(Base, AuditMixin):
    __tablename__ = 'feature_flag_master'
    feature_flag_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feature_code: Mapped[str] = mapped_column(String(150), unique=True)
    feature_name: Mapped[str] = mapped_column(String(300))
    module_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_status: Mapped[bool] = mapped_column(Boolean, default=False)
    rollout_mode: Mapped[str] = mapped_column(String(50), default='GLOBAL')
    effective_from: Mapped[str | None] = mapped_column(String(30), nullable=True)
    effective_to: Mapped[str | None] = mapped_column(String(30), nullable=True)


class FeatureFlagScope(Base, AuditMixin):
    __tablename__ = 'feature_flag_scope'
    scope_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feature_flag_id: Mapped[int] = mapped_column(Integer)
    scope_type: Mapped[str] = mapped_column(String(30))
    scope_reference_id: Mapped[str] = mapped_column(String(100))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class MonitoringPolicyMaster(Base, AuditMixin):
    __tablename__ = 'monitoring_policy_master'
    policy_master_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(200))
    policy_type: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MonitoringPolicyVersion(Base, AuditMixin):
    __tablename__ = 'monitoring_policy_version'
    policy_version_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_master_id: Mapped[int] = mapped_column(Integer)
    version_no: Mapped[str] = mapped_column(String(40))
    policy_text: Mapped[str] = mapped_column(Text)
    effective_from: Mapped[str] = mapped_column(String(30))


class EmployeePolicyAcceptance(Base):
    __tablename__ = 'employee_policy_acceptance'
    acceptance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_version_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(Integer)
    device_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accepted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acceptance_mode: Mapped[str] = mapped_column(String(30), default='WEB')
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)


class ImportJobMaster(Base, AuditMixin):
    __tablename__ = 'import_job_master'
    import_job_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_type: Mapped[str] = mapped_column(String(50))
    file_name: Mapped[str] = mapped_column(String(300))
    uploaded_by: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(30), default='UPLOADED')
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    success_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)


class ImportJobDetail(Base):
    __tablename__ = 'import_job_detail'
    import_job_detail_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_job_id: Mapped[int] = mapped_column(Integer)
    row_no: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='PENDING')


class ImportErrorLog(Base):
    __tablename__ = 'import_error_log'
    import_error_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_job_id: Mapped[int] = mapped_column(Integer)
    row_no: Mapped[int] = mapped_column(Integer)
    error_message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ApiKeyMaster(Base, AuditMixin):
    __tablename__ = 'api_key_master'
    api_key_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key_name: Mapped[str] = mapped_column(String(120), unique=True)
    key_hash: Mapped[str] = mapped_column(String(256))
    owner_user_id: Mapped[int] = mapped_column(Integer)
    scope_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='ACTIVE')
    expires_at: Mapped[str | None] = mapped_column(String(30), nullable=True)


class WebhookSubscription(Base, AuditMixin):
    __tablename__ = 'webhook_subscription'
    subscription_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_code: Mapped[str] = mapped_column(String(120))
    endpoint_url: Mapped[str] = mapped_column(String(400))
    auth_type: Mapped[str] = mapped_column(String(30), default='NONE')
    auth_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_policy_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='ACTIVE')


class WebhookDeliveryLog(Base):
    __tablename__ = 'webhook_delivery_log'
    delivery_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(Integer)
    event_code: Mapped[str] = mapped_column(String(120))
    payload_json: Mapped[str] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivery_status: Mapped[str] = mapped_column(String(30))
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)


class WebhookRetryLog(Base):
    __tablename__ = 'webhook_retry_log'
    webhook_retry_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_id: Mapped[int] = mapped_column(Integer)
    retry_no: Mapped[int] = mapped_column(Integer)
    retry_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    retry_status: Mapped[str] = mapped_column(String(30))


class ImpersonationSession(Base, AuditMixin):
    __tablename__ = 'impersonation_session'
    impersonation_session_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(Integer)
    target_user_id: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    session_status: Mapped[str] = mapped_column(String(30), default='ACTIVE')


class ImpersonationAuditLog(Base):
    __tablename__ = 'impersonation_audit_log'
    impersonation_audit_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    impersonation_session_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(120))
    action_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ArchivalPolicy(Base, AuditMixin):
    __tablename__ = 'archival_policy'
    archival_policy_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(120), unique=True)
    hot_retention_days: Mapped[int] = mapped_column(Integer)
    warm_retention_days: Mapped[int] = mapped_column(Integer)
    archive_retention_type: Mapped[str] = mapped_column(String(30), default='INDEFINITE')
    purge_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ArchivalJob(Base):
    __tablename__ = 'archival_job'
    archival_job_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(120))
    run_started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    run_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    moved_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default='RUNNING')


class ArchivalLog(Base):
    __tablename__ = 'archival_log'
    archival_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    archival_job_id: Mapped[int] = mapped_column(Integer)
    record_reference: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(60))
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RestoreRequestLog(Base, AuditMixin):
    __tablename__ = 'restore_request_log'
    restore_request_log_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(120))
    record_reference: Mapped[str] = mapped_column(String(200))
    reason: Mapped[str] = mapped_column(Text)
    request_status: Mapped[str] = mapped_column(String(30), default='REQUESTED')
