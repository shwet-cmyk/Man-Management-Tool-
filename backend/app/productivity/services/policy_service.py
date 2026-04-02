from __future__ import annotations
from datetime import datetime, UTC
from app.productivity.repositories.productivity_policy_repository import ProductivityPolicyRepository

class PolicyService:
    def __init__(self, repo: ProductivityPolicyRepository) -> None:
        self.repo = repo

    async def upsert(self, payload: dict) -> dict:
        return await self.repo.insert({**payload, 'effective_from': datetime.now(UTC), 'is_active': True})

    async def current_for_user(self, user_id: int) -> dict:
        policies = await self.repo.list_all()
        if policies:
            return policies[-1]
        return {
            'id': 0,
            'policy_name': 'Default Global',
            'scope_type': 'GLOBAL',
            'scope_reference_id': None,
            'idle_threshold_minutes': 5,
            'productive_target_hours': 8,
            'borderline_lower_hours': 6,
            'underproductive_lower_hours': 6,
            'warn_on_blacklisted_url': True,
            'block_blacklisted_url': False,
            'effective_from': datetime.now(UTC),
        }
