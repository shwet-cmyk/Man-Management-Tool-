from __future__ import annotations
from datetime import datetime, UTC
from app.productivity.repositories.device_repository import DeviceRepository

class DeviceService:
    def __init__(self, repo: DeviceRepository) -> None:
        self.repo = repo

    async def register_device(self, payload: dict) -> dict:
        existing = [d for d in await self.repo.list_all() if d['device_uuid'] == payload['device_uuid'] and d.get('is_active', True)]
        if existing:
            return existing[0]
        return await self.repo.insert({
            'device_uuid': payload['device_uuid'],
            'device_name': payload['device_name'],
            'device_type': payload.get('device_type'),
            'os_name': payload.get('os_name'),
            'os_version': payload.get('os_version'),
            'employee_user_id': payload['user_id'],
            'company_id': payload.get('company_id', 1),
            'branch_id': payload.get('branch_id'),
            'department_id': payload.get('department_id'),
            'agent_version': payload.get('agent_version'),
            'registration_status': 'ACTIVE',
            'last_heartbeat_at': None,
            'registered_at': datetime.now(UTC),
            'is_active': True,
        })

    async def list_devices(self) -> list[dict]:
        return await self.repo.list_all()

    async def deactivate(self, device_id: int) -> bool:
        row = await self.repo.update(device_id, {'is_active': False, 'registration_status': 'INACTIVE'})
        return row is not None
