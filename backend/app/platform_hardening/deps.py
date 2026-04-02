from app.platform_hardening.repositories import (
    ApiKeyRepository,
    ArchivalJobRepository,
    ArchivalLogRepository,
    ArchivalPolicyRepository,
    ExceptionApprovalLogRepository,
    ExceptionRegisterRepository,
    FeatureFlagRepository,
    FeatureFlagScopeRepository,
    GlobalSearchIndexRepository,
    GlobalSearchLogRepository,
    ImpersonationAuditLogRepository,
    ImpersonationSessionRepository,
    ImportErrorLogRepository,
    ImportJobDetailRepository,
    ImportJobRepository,
    MonitoringPolicyMasterRepository,
    MonitoringPolicyVersionRepository,
    PolicyAcceptanceRepository,
    RestoreRequestLogRepository,
    SettingsChangeLogRepository,
    SettingsGroupRepository,
    SettingsRegistryRepository,
    WebhookDeliveryLogRepository,
    WebhookRetryLogRepository,
    WebhookSubscriptionRepository,
)
from app.platform_hardening.services import (
    ApiWebhookGovernanceService,
    DataArchivalService,
    ExceptionRegisterService,
    FeatureFlagService,
    GlobalSearchService,
    ImpersonationService,
    ImportMigrationService,
    MonitoringConsentService,
    SettingsRegistryService,
)

search_index_repo = GlobalSearchIndexRepository()
search_log_repo = GlobalSearchLogRepository()
settings_group_repo = SettingsGroupRepository()
settings_repo = SettingsRegistryRepository()
settings_change_repo = SettingsChangeLogRepository()
exception_repo = ExceptionRegisterRepository()
exception_approval_repo = ExceptionApprovalLogRepository()
feature_flag_repo = FeatureFlagRepository()
feature_scope_repo = FeatureFlagScopeRepository()
monitoring_master_repo = MonitoringPolicyMasterRepository()
monitoring_version_repo = MonitoringPolicyVersionRepository()
acceptance_repo = PolicyAcceptanceRepository()
import_job_repo = ImportJobRepository()
import_detail_repo = ImportJobDetailRepository()
import_error_repo = ImportErrorLogRepository()
api_key_repo = ApiKeyRepository()
webhook_sub_repo = WebhookSubscriptionRepository()
webhook_delivery_repo = WebhookDeliveryLogRepository()
webhook_retry_repo = WebhookRetryLogRepository()
impersonation_session_repo = ImpersonationSessionRepository()
impersonation_audit_repo = ImpersonationAuditLogRepository()
archival_policy_repo = ArchivalPolicyRepository()
archival_job_repo = ArchivalJobRepository()
archival_log_repo = ArchivalLogRepository()
restore_repo = RestoreRequestLogRepository()

search_service = GlobalSearchService(search_index_repo, search_log_repo)
settings_service = SettingsRegistryService(settings_repo, settings_change_repo)
exception_service = ExceptionRegisterService(exception_repo, exception_approval_repo)
feature_flag_service = FeatureFlagService(feature_flag_repo, feature_scope_repo)
monitoring_service = MonitoringConsentService(monitoring_master_repo, monitoring_version_repo, acceptance_repo)
import_service = ImportMigrationService(import_job_repo, import_detail_repo, import_error_repo)
api_webhook_service = ApiWebhookGovernanceService(api_key_repo, webhook_sub_repo, webhook_delivery_repo, webhook_retry_repo)
impersonation_service = ImpersonationService(impersonation_session_repo, impersonation_audit_repo)
archival_service = DataArchivalService(archival_policy_repo, archival_job_repo, archival_log_repo, restore_repo)
