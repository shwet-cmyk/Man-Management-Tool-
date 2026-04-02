from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from fastapi import HTTPException

from app.core.integration_hooks import emit_audit_event, emit_notification_event
from app.modules.rbac.privileges import is_granted


class GlobalSearchService:
    def __init__(self, index_repo, log_repo) -> None:
        self.index_repo = index_repo
        self.log_repo = log_repo

    async def index_record(self, payload: dict, actor_user_id: int) -> dict:
        row = await self.index_repo.insert({**payload, 'is_active': payload.get('is_active', True), 'created_at': datetime.now(UTC)})
        emit_audit_event('global_search_index_upsert', {'actor_user_id': actor_user_id, 'search_index_id': row['id']})
        return row

    async def search(self, *, user_id: int, role: str, query_text: str) -> dict:
        if len(query_text.strip()) < 2:
            raise HTTPException(status_code=422, detail='Query length must be at least 2 characters')
        hits = await self.index_repo.search(query_text)
        visible = [r for r in hits if is_granted(role, r['privilege_code'])]
        groups: dict[str, list[dict]] = {}
        for row in visible:
            groups.setdefault(row['module_name'], []).append(row)
        await self.log_repo.insert({'user_id': user_id, 'query_text': query_text, 'result_count': len(visible), 'clicked_result_id': None, 'searched_at': datetime.now(UTC)})
        emit_audit_event('global_search_executed', {'user_id': user_id, 'query_text': query_text, 'result_count': len(visible)})
        return {'query_text': query_text, 'result_count': len(visible), 'groups': groups}

    async def click_result(self, *, user_id: int, search_log_id: int, clicked_result_id: int) -> dict:
        row = await self.log_repo.update(search_log_id, {'clicked_result_id': clicked_result_id})
        if not row:
            raise HTTPException(status_code=404, detail='Search log not found')
        emit_audit_event('global_search_result_clicked', {'user_id': user_id, 'search_log_id': search_log_id, 'clicked_result_id': clicked_result_id})
        return row


class SettingsRegistryService:
    def __init__(self, settings_repo, change_repo) -> None:
        self.settings_repo = settings_repo
        self.change_repo = change_repo

    async def upsert_setting(self, payload: dict, actor_user_id: int, actor_role: str) -> dict:
        existing = await self.settings_repo.by_key(payload['setting_key'])
        if existing and not existing.get('is_editable', True) and actor_role != 'SuperAdmin':
            raise HTTPException(status_code=403, detail='Restricted setting can be edited only by SuperAdmin')
        self._validate_type(payload['setting_value'], payload['value_type'])
        if existing:
            old_val = existing['setting_value']
            updated = await self.settings_repo.update(existing['id'], {**payload, 'updated_by': actor_user_id, 'updated_at': datetime.now(UTC)})
            await self.change_repo.insert({'setting_id': updated['id'], 'changed_by': actor_user_id, 'old_value': old_val, 'new_value': updated['setting_value'], 'changed_at': datetime.now(UTC)})
            emit_audit_event('settings_registry_updated', {'setting_id': updated['id'], 'changed_by': actor_user_id})
            return updated
        created = await self.settings_repo.insert({**payload, 'created_by': actor_user_id, 'updated_by': actor_user_id, 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC)})
        await self.change_repo.insert({'setting_id': created['id'], 'changed_by': actor_user_id, 'old_value': None, 'new_value': created['setting_value'], 'changed_at': datetime.now(UTC)})
        emit_audit_event('settings_registry_created', {'setting_id': created['id'], 'changed_by': actor_user_id})
        return created

    @staticmethod
    def _validate_type(value: str, value_type: str) -> None:
        try:
            if value_type == 'INT':
                int(value)
            elif value_type == 'FLOAT':
                float(value)
            elif value_type == 'BOOL':
                if value.lower() not in {'true', 'false', '1', '0'}:
                    raise ValueError('invalid bool')
            elif value_type == 'JSON':
                import json
                json.loads(value)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f'Invalid setting value for type {value_type}') from exc


class ExceptionRegisterService:
    def __init__(self, exception_repo, approval_log_repo) -> None:
        self.exception_repo = exception_repo
        self.approval_log_repo = approval_log_repo

    async def create_exception(self, payload: dict) -> dict:
        if payload['start_date'] > payload['end_date']:
            raise HTTPException(status_code=422, detail='start_date cannot be after end_date')
        for existing in await self.exception_repo.list_all():
            if existing['employee_user_id'] == payload['employee_user_id'] and existing['exception_type'] == payload['exception_type'] and existing['status'] in {'PENDING', 'APPROVED'}:
                if not (payload['end_date'] < existing['start_date'] or payload['start_date'] > existing['end_date']):
                    raise HTTPException(status_code=409, detail='Overlapping exception exists')
        row = await self.exception_repo.insert({**payload, 'status': 'PENDING', 'approved_by': None, 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC), 'created_by': payload['requested_by'], 'updated_by': payload['requested_by']})
        emit_audit_event('exception_created', {'exception_id': row['id'], 'requested_by': payload['requested_by']})
        emit_notification_event('exception_pending_approval', {'exception_id': row['id']})
        return row

    async def action_exception(self, exception_id: int, payload: dict) -> dict:
        row = await self.exception_repo.update(exception_id, {'status': 'APPROVED' if payload['action'] == 'APPROVE' else 'REJECTED', 'approved_by': payload['actor_user_id'], 'updated_by': payload['actor_user_id'], 'updated_at': datetime.now(UTC)})
        if not row:
            raise HTTPException(status_code=404, detail='Exception not found')
        await self.approval_log_repo.insert({'exception_id': exception_id, 'actor_user_id': payload['actor_user_id'], 'action': payload['action'], 'remarks': payload.get('remarks'), 'action_at': datetime.now(UTC)})
        emit_audit_event('exception_actioned', {'exception_id': exception_id, 'action': payload['action']})
        return row


class FeatureFlagService:
    def __init__(self, flag_repo, scope_repo) -> None:
        self.flag_repo = flag_repo
        self.scope_repo = scope_repo

    async def create_flag(self, payload: dict, actor_user_id: int) -> dict:
        if await self.flag_repo.by_code(payload['feature_code']):
            raise HTTPException(status_code=409, detail='feature_code already exists')
        if payload.get('effective_from') and payload.get('effective_to') and payload['effective_from'] > payload['effective_to']:
            raise HTTPException(status_code=422, detail='Invalid effective date range')
        row = await self.flag_repo.insert({**payload, 'created_by': actor_user_id, 'updated_by': actor_user_id, 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC)})
        emit_audit_event('feature_flag_created', {'feature_flag_id': row['id'], 'feature_code': row['feature_code']})
        return row

    async def add_scope(self, feature_flag_id: int, payload: dict, actor_user_id: int) -> dict:
        if not await self.flag_repo.get(feature_flag_id):
            raise HTTPException(status_code=404, detail='Feature flag not found')
        row = await self.scope_repo.insert({**payload, 'feature_flag_id': feature_flag_id, 'created_by': actor_user_id, 'updated_by': actor_user_id, 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC)})
        emit_audit_event('feature_flag_scope_added', {'feature_flag_id': feature_flag_id, 'scope_id': row['id']})
        return row


class MonitoringConsentService:
    def __init__(self, master_repo, version_repo, acceptance_repo) -> None:
        self.master_repo = master_repo
        self.version_repo = version_repo
        self.acceptance_repo = acceptance_repo

    async def create_policy(self, payload: dict, actor_user_id: int) -> dict:
        row = await self.master_repo.insert({**payload, 'created_by': actor_user_id, 'updated_by': actor_user_id, 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC)})
        emit_audit_event('monitoring_policy_created', {'policy_master_id': row['id']})
        return row

    async def publish_policy_version(self, payload: dict, actor_user_id: int) -> dict:
        row = await self.version_repo.insert({**payload, 'created_by': actor_user_id, 'updated_by': actor_user_id, 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC)})
        emit_notification_event('monitoring_policy_published', {'policy_version_id': row['id']})
        return row

    async def accept_policy(self, payload: dict) -> dict:
        row = await self.acceptance_repo.insert({**payload, 'accepted_at': datetime.now(UTC)})
        emit_audit_event('monitoring_policy_accepted', {'user_id': payload['user_id'], 'policy_version_id': payload['policy_version_id']})
        return row


class ImportMigrationService:
    def __init__(self, job_repo, detail_repo, error_repo) -> None:
        self.job_repo = job_repo
        self.detail_repo = detail_repo
        self.error_repo = error_repo

    async def create_job(self, payload: dict) -> dict:
        rows = payload.pop('rows', [])
        job = await self.job_repo.insert({**payload, 'status': 'VALIDATING', 'total_rows': len(rows), 'success_rows': 0, 'failed_rows': 0, 'uploaded_at': datetime.now(UTC), 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC), 'created_by': payload['uploaded_by'], 'updated_by': payload['uploaded_by']})
        success = 0
        failed = 0
        for idx, row in enumerate(rows, start=1):
            await self.detail_repo.insert({'import_job_id': job['id'], 'row_no': idx, 'payload_json': str(row), 'status': 'SUCCESS'})
            if not row:
                failed += 1
                await self.error_repo.insert({'import_job_id': job['id'], 'row_no': idx, 'error_message': 'Empty row', 'created_at': datetime.now(UTC)})
            else:
                success += 1
        status = 'COMPLETED' if failed == 0 else 'PARTIAL_FAILURE'
        return await self.job_repo.update(job['id'], {'status': status, 'success_rows': success, 'failed_rows': failed, 'updated_at': datetime.now(UTC)})


class ApiWebhookGovernanceService:
    def __init__(self, api_key_repo, sub_repo, delivery_repo, retry_repo) -> None:
        self.api_key_repo = api_key_repo
        self.sub_repo = sub_repo
        self.delivery_repo = delivery_repo
        self.retry_repo = retry_repo

    async def create_api_key(self, payload: dict, actor_user_id: int) -> dict:
        if await self.api_key_repo.by_name(payload['key_name']):
            raise HTTPException(status_code=409, detail='API key name already exists')
        key_hash = sha256(f"{payload['key_name']}:{payload['owner_user_id']}:{datetime.now(UTC).isoformat()}".encode()).hexdigest()
        row = await self.api_key_repo.insert({**payload, 'key_hash': key_hash, 'status': 'ACTIVE', 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC), 'created_by': actor_user_id, 'updated_by': actor_user_id})
        emit_audit_event('api_key_created', {'api_key_id': row['id']})
        return row

    async def create_webhook_subscription(self, payload: dict, actor_user_id: int) -> dict:
        row = await self.sub_repo.insert({**payload, 'status': 'ACTIVE', 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC), 'created_by': actor_user_id, 'updated_by': actor_user_id})
        emit_audit_event('webhook_subscription_created', {'subscription_id': row['id']})
        return row

    async def log_delivery(self, payload: dict) -> dict:
        row = await self.delivery_repo.insert({**payload, 'attempted_at': datetime.now(UTC)})
        if row['delivery_status'] == 'FAILED':
            await self.retry_repo.insert({'delivery_id': row['id'], 'retry_no': 1, 'retry_at': datetime.now(UTC), 'retry_status': 'SCHEDULED'})
        return row


class ImpersonationService:
    def __init__(self, session_repo, audit_repo) -> None:
        self.session_repo = session_repo
        self.audit_repo = audit_repo

    async def start_session(self, payload: dict, actor_role: str) -> dict:
        if actor_role not in {'Admin', 'SuperAdmin'}:
            raise HTTPException(status_code=403, detail='Only Admin/SuperAdmin can impersonate')
        existing = await self.session_repo.active_for_admin(payload['admin_user_id'])
        if existing:
            raise HTTPException(status_code=409, detail='Admin already has active impersonation session')
        session = await self.session_repo.insert({**payload, 'started_at': datetime.now(UTC), 'ended_at': None, 'session_status': 'ACTIVE', 'created_by': payload['admin_user_id'], 'updated_by': payload['admin_user_id'], 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC)})
        await self.audit_repo.insert({'impersonation_session_id': session['id'], 'action': 'START', 'action_at': datetime.now(UTC), 'metadata_json': None})
        emit_audit_event('impersonation_started', {'impersonation_session_id': session['id']})
        return session

    async def end_session(self, session_id: int, actor_user_id: int) -> dict:
        row = await self.session_repo.update(session_id, {'session_status': 'ENDED', 'ended_at': datetime.now(UTC), 'updated_by': actor_user_id, 'updated_at': datetime.now(UTC)})
        if not row:
            raise HTTPException(status_code=404, detail='Impersonation session not found')
        await self.audit_repo.insert({'impersonation_session_id': session_id, 'action': 'END', 'action_at': datetime.now(UTC), 'metadata_json': None})
        emit_audit_event('impersonation_ended', {'impersonation_session_id': session_id})
        return row


class DataArchivalService:
    def __init__(self, policy_repo, job_repo, log_repo, restore_repo) -> None:
        self.policy_repo = policy_repo
        self.job_repo = job_repo
        self.log_repo = log_repo
        self.restore_repo = restore_repo

    async def upsert_policy(self, payload: dict, actor_user_id: int) -> dict:
        existing = await self.policy_repo.by_entity(payload['entity_name'])
        if existing:
            row = await self.policy_repo.update(existing['id'], {**payload, 'updated_by': actor_user_id, 'updated_at': datetime.now(UTC)})
        else:
            row = await self.policy_repo.insert({**payload, 'created_by': actor_user_id, 'updated_by': actor_user_id, 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC)})
        emit_audit_event('archival_policy_upsert', {'entity_name': row['entity_name']})
        return row

    async def run_archival(self, entity_name: str, actor_user_id: int) -> dict:
        policy = await self.policy_repo.by_entity(entity_name)
        if not policy:
            raise HTTPException(status_code=404, detail='Archival policy for entity not found')
        job = await self.job_repo.insert({'entity_name': entity_name, 'run_started_at': datetime.now(UTC), 'run_completed_at': datetime.now(UTC), 'moved_count': 0, 'status': 'COMPLETED'})
        await self.log_repo.insert({'archival_job_id': job['id'], 'record_reference': f'{entity_name}:batch', 'action': 'MOVE_TO_ARCHIVE', 'logged_at': datetime.now(UTC)})
        emit_audit_event('archival_job_completed', {'archival_job_id': job['id'], 'entity_name': entity_name})
        return job

    async def request_restore(self, payload: dict) -> dict:
        row = await self.restore_repo.insert({**payload, 'request_status': 'REQUESTED', 'created_at': datetime.now(UTC), 'updated_at': datetime.now(UTC), 'updated_by': payload['created_by']})
        emit_notification_event('archival_restore_requested', {'restore_request_log_id': row['id'], 'entity_name': row['entity_name']})
        return row
