from __future__ import annotations
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from app.productivity.repositories.agent_registration_repository import AgentRegistrationRepository

class AgentRegistrationService:
    def __init__(self, repo: AgentRegistrationRepository) -> None:
        self.repo = repo

    async def create_or_refresh(self, device_id: int, user_id: int) -> dict:
        token = f"agent-{uuid4()}"
        return await self.repo.insert({
            'device_id': device_id,
            'user_id': user_id,
            'registration_token': token,
            'token_expires_at': datetime.now(UTC) + timedelta(days=30),
            'agent_status': 'ACTIVE',
            'last_sync_at': None,
            'last_error': None,
            'created_at': datetime.now(UTC),
        })
