from __future__ import annotations

from app.core.inmemory_repo import InMemoryRepo


class GlobalSearchIndexRepository(InMemoryRepo):
    async def search(self, query: str) -> list[dict]:
        query_lower = query.lower()
        return [r for r in await self.list_all() if r.get('is_active', True) and query_lower in r.get('searchable_text', '').lower()]


class GlobalSearchLogRepository(InMemoryRepo):
    pass


class SettingsGroupRepository(InMemoryRepo):
    pass


class SettingsRegistryRepository(InMemoryRepo):
    async def by_key(self, setting_key: str) -> dict | None:
        for row in await self.list_all():
            if row['setting_key'] == setting_key:
                return row
        return None


class SettingsChangeLogRepository(InMemoryRepo):
    pass


class ExceptionRegisterRepository(InMemoryRepo):
    async def active_for_employee(self, employee_user_id: int) -> list[dict]:
        return [r for r in await self.list_all() if r['employee_user_id'] == employee_user_id and r['status'] == 'APPROVED']


class ExceptionApprovalLogRepository(InMemoryRepo):
    pass


class FeatureFlagRepository(InMemoryRepo):
    async def by_code(self, feature_code: str) -> dict | None:
        for row in await self.list_all():
            if row['feature_code'] == feature_code:
                return row
        return None


class FeatureFlagScopeRepository(InMemoryRepo):
    async def by_feature(self, feature_flag_id: int) -> list[dict]:
        return [r for r in await self.list_all() if r['feature_flag_id'] == feature_flag_id]


class MonitoringPolicyMasterRepository(InMemoryRepo):
    pass


class MonitoringPolicyVersionRepository(InMemoryRepo):
    async def latest_version(self, policy_master_id: int) -> dict | None:
        rows = [r for r in await self.list_all() if r['policy_master_id'] == policy_master_id]
        if not rows:
            return None
        return sorted(rows, key=lambda x: x['id'], reverse=True)[0]


class PolicyAcceptanceRepository(InMemoryRepo):
    pass


class ImportJobRepository(InMemoryRepo):
    pass


class ImportJobDetailRepository(InMemoryRepo):
    pass


class ImportErrorLogRepository(InMemoryRepo):
    pass


class ApiKeyRepository(InMemoryRepo):
    async def by_name(self, key_name: str) -> dict | None:
        for row in await self.list_all():
            if row['key_name'] == key_name:
                return row
        return None


class WebhookSubscriptionRepository(InMemoryRepo):
    pass


class WebhookDeliveryLogRepository(InMemoryRepo):
    pass


class WebhookRetryLogRepository(InMemoryRepo):
    pass


class ImpersonationSessionRepository(InMemoryRepo):
    async def active_for_admin(self, admin_user_id: int) -> dict | None:
        for row in await self.list_all():
            if row['admin_user_id'] == admin_user_id and row['session_status'] == 'ACTIVE':
                return row
        return None


class ImpersonationAuditLogRepository(InMemoryRepo):
    pass


class ArchivalPolicyRepository(InMemoryRepo):
    async def by_entity(self, entity_name: str) -> dict | None:
        for row in await self.list_all():
            if row['entity_name'] == entity_name:
                return row
        return None


class ArchivalJobRepository(InMemoryRepo):
    pass


class ArchivalLogRepository(InMemoryRepo):
    pass


class RestoreRequestLogRepository(InMemoryRepo):
    pass
