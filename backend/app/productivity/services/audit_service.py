from __future__ import annotations

from datetime import datetime, UTC
from app.productivity.repositories.productivity_audit_repository import ProductivityAuditRepository


class AuditService:
    def __init__(self, repo: ProductivityAuditRepository) -> None:
        self.repo = repo

    async def log(self, *, user_id: int | None, action_type: str, target_entity: str, target_id: int | None = None, field_name: str | None = None, old_value: str | None = None, new_value: str | None = None, remarks: str | None = None) -> dict:
        return await self.repo.insert(
            {
                'user_id': user_id,
                'action_type': action_type,
                'target_entity': target_entity,
                'target_id': target_id,
                'field_name': field_name,
                'old_value': old_value,
                'new_value': new_value,
                'remarks': remarks,
                'action_timestamp': datetime.now(UTC),
            }
        )

    async def list_all(self) -> list[dict]:
        return await self.repo.list_all()
