from __future__ import annotations

from datetime import datetime, UTC

from fastapi import APIRouter, Depends

from app.core.authz import require_permission
from app.platform_hardening.deps import (
    acceptance_repo,
    api_key_repo,
    api_webhook_service,
    archival_job_repo,
    archival_policy_repo,
    archival_service,
    exception_repo,
    exception_service,
    feature_flag_repo,
    feature_flag_service,
    feature_scope_repo,
    impersonation_service,
    import_error_repo,
    import_job_repo,
    import_service,
    monitoring_service,
    search_log_repo,
    search_service,
    settings_change_repo,
    settings_repo,
    settings_service,
    webhook_delivery_repo,
)
from app.platform_hardening.schemas import (
    ApiKeyCreate,
    ArchivalPolicyUpsert,
    ExceptionAction,
    ExceptionCreate,
    FeatureFlagCreate,
    FeatureScopeUpsert,
    GenericReportResponse,
    ImpersonationStart,
    ImportJobCreate,
    MonitoringPolicyCreate,
    MonitoringPolicyVersionCreate,
    PolicyAcceptanceCreate,
    RestoreRequestCreate,
    SearchIndexUpsert,
    SearchQueryRequest,
    SearchQueryResponse,
    SettingUpsert,
    WebhookSubscriptionCreate,
)

router = APIRouter(prefix='/platform-hardening', tags=['Platform Hardening'])

# Module 1: Global Search
@router.post('/global-search/index', dependencies=[Depends(require_permission('global_search.write'))])
async def global_search_index(payload: SearchIndexUpsert, actor_user_id: int = 1):
    return await search_service.index_record(payload.model_dump(), actor_user_id)


@router.post('/global-search/query', response_model=SearchQueryResponse, dependencies=[Depends(require_permission('global_search.read'))])
async def global_search_query(payload: SearchQueryRequest):
    return await search_service.search(**payload.model_dump())


@router.post('/global-search/log/{search_log_id}/click', dependencies=[Depends(require_permission('global_search.read'))])
async def global_search_click(search_log_id: int, clicked_result_id: int, user_id: int):
    return await search_service.click_result(user_id=user_id, search_log_id=search_log_id, clicked_result_id=clicked_result_id)


@router.get('/global-search/reports/usage', response_model=GenericReportResponse, dependencies=[Depends(require_permission('global_search.report'))])
async def global_search_usage_report():
    rows = await search_log_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}


@router.get('/global-search/analytics/top-queries', dependencies=[Depends(require_permission('global_search.analytics'))])
async def global_search_top_queries():
    counts: dict[str, int] = {}
    for row in await search_log_repo.list_all():
        counts[row['query_text']] = counts.get(row['query_text'], 0) + 1
    return {'generated_at': datetime.now(UTC), 'top_queries': sorted(counts.items(), key=lambda x: x[1], reverse=True)}

# Module 2: Master Settings Registry
@router.post('/settings-registry', dependencies=[Depends(require_permission('settings_registry.write'))])
async def upsert_setting(payload: SettingUpsert, actor_user_id: int, actor_role: str):
    return await settings_service.upsert_setting(payload.model_dump(), actor_user_id, actor_role)


@router.get('/settings-registry', dependencies=[Depends(require_permission('settings_registry.read'))])
async def list_settings(module_name: str | None = None):
    rows = await settings_repo.list_all()
    if module_name:
        rows = [r for r in rows if r['module_name'].lower() == module_name.lower()]
    return rows


@router.get('/settings-registry/reports/changes', response_model=GenericReportResponse, dependencies=[Depends(require_permission('settings_registry.report'))])
async def settings_change_report():
    rows = await settings_change_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}


@router.get('/settings-registry/analytics/unstable', dependencies=[Depends(require_permission('settings_registry.analytics'))])
async def settings_unstable_analytics():
    counts: dict[int, int] = {}
    for row in await settings_change_repo.list_all():
        counts[row['setting_id']] = counts.get(row['setting_id'], 0) + 1
    return {'generated_at': datetime.now(UTC), 'setting_change_frequency': sorted(counts.items(), key=lambda x: x[1], reverse=True)}

# Module 3: Exception Register
@router.post('/exceptions', dependencies=[Depends(require_permission('exception_register.write'))])
async def create_exception(payload: ExceptionCreate):
    return await exception_service.create_exception(payload.model_dump())


@router.post('/exceptions/{exception_id}/action', dependencies=[Depends(require_permission('exception_register.approve'))])
async def action_exception(exception_id: int, payload: ExceptionAction):
    return await exception_service.action_exception(exception_id, payload.model_dump())


@router.get('/exceptions/reports/active', response_model=GenericReportResponse, dependencies=[Depends(require_permission('exception_register.report'))])
async def active_exceptions_report():
    rows = [r for r in await exception_repo.list_all() if r['status'] == 'APPROVED']
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}


@router.get('/exceptions/analytics/by-type', dependencies=[Depends(require_permission('exception_register.analytics'))])
async def exceptions_analytics_by_type():
    grouped: dict[str, int] = {}
    for row in await exception_repo.list_all():
        grouped[row['exception_type']] = grouped.get(row['exception_type'], 0) + 1
    return {'generated_at': datetime.now(UTC), 'exception_type_distribution': grouped}

# Module 4: Feature Flag / UAT
@router.post('/feature-flags', dependencies=[Depends(require_permission('feature_flag.write'))])
async def create_feature_flag(payload: FeatureFlagCreate, actor_user_id: int):
    return await feature_flag_service.create_flag(payload.model_dump(), actor_user_id)


@router.post('/feature-flags/{feature_flag_id}/scopes', dependencies=[Depends(require_permission('feature_flag.write'))])
async def add_feature_scope(feature_flag_id: int, payload: FeatureScopeUpsert, actor_user_id: int):
    return await feature_flag_service.add_scope(feature_flag_id, payload.model_dump(), actor_user_id)


@router.get('/feature-flags/reports/active', response_model=GenericReportResponse, dependencies=[Depends(require_permission('feature_flag.report'))])
async def feature_flags_report():
    rows = [r for r in await feature_flag_repo.list_all() if r.get('is_active', True)]
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}


@router.get('/feature-flags/analytics/adoption', dependencies=[Depends(require_permission('feature_flag.analytics'))])
async def feature_flags_analytics():
    scopes = await feature_scope_repo.list_all()
    by_scope: dict[str, int] = {}
    for row in scopes:
        by_scope[row['scope_type']] = by_scope.get(row['scope_type'], 0) + 1
    return {'generated_at': datetime.now(UTC), 'rollout_scope_distribution': by_scope}

# Module 5: Monitoring Consent / Disclosure
@router.post('/monitoring/policies', dependencies=[Depends(require_permission('monitoring_consent.write'))])
async def create_policy(payload: MonitoringPolicyCreate, actor_user_id: int):
    return await monitoring_service.create_policy(payload.model_dump(), actor_user_id)


@router.post('/monitoring/policies/versions', dependencies=[Depends(require_permission('monitoring_consent.write'))])
async def publish_policy_version(payload: MonitoringPolicyVersionCreate, actor_user_id: int):
    return await monitoring_service.publish_policy_version(payload.model_dump(), actor_user_id)


@router.post('/monitoring/policies/acceptance', dependencies=[Depends(require_permission('monitoring_consent.write'))])
async def accept_policy(payload: PolicyAcceptanceCreate):
    return await monitoring_service.accept_policy(payload.model_dump())


@router.get('/monitoring/reports/acceptance', response_model=GenericReportResponse, dependencies=[Depends(require_permission('monitoring_consent.report'))])
async def monitoring_acceptance_report():
    rows = await acceptance_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}

# Module 6: Import / Migration
@router.post('/import/jobs', dependencies=[Depends(require_permission('import_migration.write'))])
async def create_import_job(payload: ImportJobCreate):
    return await import_service.create_job(payload.model_dump())


@router.get('/import/jobs/reports/history', response_model=GenericReportResponse, dependencies=[Depends(require_permission('import_migration.report'))])
async def import_history_report():
    rows = await import_job_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}


@router.get('/import/jobs/analytics/failure-patterns', dependencies=[Depends(require_permission('import_migration.analytics'))])
async def import_failure_analytics():
    errors = await import_error_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'failed_row_count': len(errors), 'sample': errors[:25]}

# Module 7: API / Webhook Governance
@router.post('/integration-governance/api-keys', dependencies=[Depends(require_permission('webhook_governance.write'))])
async def create_api_key(payload: ApiKeyCreate, actor_user_id: int):
    return await api_webhook_service.create_api_key(payload.model_dump(), actor_user_id)


@router.post('/integration-governance/webhooks', dependencies=[Depends(require_permission('webhook_governance.write'))])
async def create_webhook(payload: WebhookSubscriptionCreate, actor_user_id: int):
    body = payload.model_dump()
    body['endpoint_url'] = str(body['endpoint_url'])
    return await api_webhook_service.create_webhook_subscription(body, actor_user_id)


@router.post('/integration-governance/webhook-delivery', dependencies=[Depends(require_permission('webhook_governance.write'))])
async def log_webhook_delivery(subscription_id: int, event_code: str, payload_json: str, delivery_status: str, response_code: int | None = None, response_body: str | None = None):
    return await api_webhook_service.log_delivery({'subscription_id': subscription_id, 'event_code': event_code, 'payload_json': payload_json, 'delivery_status': delivery_status, 'response_code': response_code, 'response_body': response_body})


@router.get('/integration-governance/reports/webhook-delivery', response_model=GenericReportResponse, dependencies=[Depends(require_permission('webhook_governance.report'))])
async def webhook_delivery_report():
    rows = await webhook_delivery_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}


@router.get('/integration-governance/analytics/api-key-usage', dependencies=[Depends(require_permission('webhook_governance.analytics'))])
async def api_key_analytics():
    rows = await api_key_repo.list_all()
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row['status']] = status_counts.get(row['status'], 0) + 1
    return {'generated_at': datetime.now(UTC), 'api_key_status_distribution': status_counts}

# Module 8: Admin View-As / Impersonation Control
@router.post('/impersonation/start', dependencies=[Depends(require_permission('impersonation_control.write'))])
async def start_impersonation(payload: ImpersonationStart, actor_role: str):
    return await impersonation_service.start_session(payload.model_dump(), actor_role)


@router.post('/impersonation/{session_id}/end', dependencies=[Depends(require_permission('impersonation_control.write'))])
async def end_impersonation(session_id: int, actor_user_id: int):
    return await impersonation_service.end_session(session_id, actor_user_id)

# Module 9: Data Archival Control
@router.post('/archival/policies', dependencies=[Depends(require_permission('data_archival.write'))])
async def upsert_archival_policy(payload: ArchivalPolicyUpsert, actor_user_id: int):
    return await archival_service.upsert_policy(payload.model_dump(), actor_user_id)


@router.post('/archival/jobs/run', dependencies=[Depends(require_permission('data_archival.run'))])
async def run_archival_job(entity_name: str, actor_user_id: int):
    return await archival_service.run_archival(entity_name, actor_user_id)


@router.post('/archival/restore-requests', dependencies=[Depends(require_permission('data_archival.write'))])
async def request_archival_restore(payload: RestoreRequestCreate):
    return await archival_service.request_restore(payload.model_dump())


@router.get('/archival/reports/jobs', response_model=GenericReportResponse, dependencies=[Depends(require_permission('data_archival.report'))])
async def archival_jobs_report():
    rows = await archival_job_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'rows': rows, 'total': len(rows)}


@router.get('/archival/analytics/storage-trend', dependencies=[Depends(require_permission('data_archival.analytics'))])
async def archival_storage_analytics():
    rows = await archival_job_repo.list_all()
    return {'generated_at': datetime.now(UTC), 'job_count': len(rows), 'moved_total': sum(x.get('moved_count', 0) for x in rows)}
