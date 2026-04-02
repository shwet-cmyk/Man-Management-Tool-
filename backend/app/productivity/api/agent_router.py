from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.productivity.api._deps import activity_ingestion_service, agent_registration_service, device_service, policy_service
from app.productivity.schemas.activity_log_schema import AgentHeartbeatRequest, AgentSyncRequest, AgentSyncResponse
from app.productivity.schemas.device_schema import DeviceRegisterRequest

router = APIRouter(prefix='/productivity/agent', tags=['Productivity Agent'])

@router.post('/register')
async def register_agent(payload: DeviceRegisterRequest):
    device = await device_service.register_device(payload.model_dump())
    registration = await agent_registration_service.create_or_refresh(device['id'], payload.user_id)
    policy = await policy_service.current_for_user(payload.user_id)
    return {'success': True, 'device_id': device['id'], 'registration_token': registration['registration_token'], 'policy_snapshot': {'idle_threshold_minutes': policy['idle_threshold_minutes'], 'productive_target_hours': policy['productive_target_hours']}}

@router.post('/heartbeat')
async def heartbeat(payload: AgentHeartbeatRequest):
    devices = await device_service.list_devices()
    if not any(d['id'] == payload.device_id and d['employee_user_id'] == payload.user_id and d.get('is_active', True) for d in devices):
        raise HTTPException(status_code=404, detail='Device not found or inactive')
    return {'success': True}

@router.post('/sync', response_model=AgentSyncResponse)
async def sync(payload: AgentSyncRequest):
    policy = await policy_service.current_for_user(payload.user_id)
    result = await activity_ingestion_service.sync(payload.device_id, payload.user_id, [e.model_dump() for e in payload.events], policy)
    return AgentSyncResponse(success=True, **result)
