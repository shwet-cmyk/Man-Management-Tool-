from __future__ import annotations

from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException

from app.productivity.api._deps import (
    activity_ingestion_service,
    agent_registration_service,
    audit_service,
    device_service,
    policy_service,
)
from app.productivity.schemas.activity_log_schema import AgentHeartbeatRequest, AgentSyncRequest, AgentSyncResponse
from app.productivity.schemas.device_schema import DeviceRegisterRequest

router = APIRouter(prefix='/productivity/agent', tags=['Productivity Agent'])


@router.post('/register')
async def register_agent(payload: DeviceRegisterRequest):
    device = await device_service.register_device(payload.model_dump())
    registration = await agent_registration_service.create_or_refresh(device['id'], payload.user_id)
    policy = await policy_service.current_for_user(payload.user_id)
    await audit_service.log(
        user_id=payload.user_id,
        action_type='AGENT_REGISTER',
        target_entity='device_master',
        target_id=device['id'],
        remarks='Device registered/refreshed via agent endpoint',
    )
    return {
        'success': True,
        'device_id': device['id'],
        'registration_token': registration['registration_token'],
        'policy_snapshot': {
            'idle_threshold_minutes': policy['idle_threshold_minutes'],
            'productive_target_hours': policy['productive_target_hours'],
            'warn_on_blacklisted_url': policy['warn_on_blacklisted_url'],
            'block_blacklisted_url': policy['block_blacklisted_url'],
        },
    }


@router.post('/heartbeat')
async def heartbeat(payload: AgentHeartbeatRequest):
    devices = await device_service.list_devices()
    matched = next((d for d in devices if d['id'] == payload.device_id and d['employee_user_id'] == payload.user_id and d.get('is_active', True)), None)
    if not matched:
        raise HTTPException(status_code=404, detail='Device not found or inactive')

    matched['last_heartbeat_at'] = payload.heartbeat_at
    await audit_service.log(
        user_id=payload.user_id,
        action_type='AGENT_HEARTBEAT',
        target_entity='device_master',
        target_id=payload.device_id,
    )
    return {'success': True}


@router.post('/sync', response_model=AgentSyncResponse)
async def sync(payload: AgentSyncRequest):
    policy = await policy_service.current_for_user(payload.user_id)
    result = await activity_ingestion_service.sync(payload.device_id, payload.user_id, [e.model_dump() for e in payload.events], policy)
    await audit_service.log(
        user_id=payload.user_id,
        action_type='AGENT_SYNC',
        target_entity='raw_activity_log',
        target_id=payload.device_id,
        remarks=f"processed={result['processed_count']} breaches={result['breach_count']}",
    )
    return AgentSyncResponse(success=True, **result)


@router.get('/health')
async def agent_health():
    devices = await device_service.list_devices()
    now = datetime.now(UTC)
    online, offline = 0, 0
    report = []
    for d in devices:
        hb = d.get('last_heartbeat_at')
        is_online = bool(hb and (now - hb).total_seconds() <= 300)
        online += 1 if is_online else 0
        offline += 0 if is_online else 1
        report.append(
            {
                'device_id': d['id'],
                'device_name': d['device_name'],
                'employee_user_id': d['employee_user_id'],
                'last_heartbeat_at': hb,
                'agent_version': d.get('agent_version'),
                'status': 'ONLINE' if is_online else 'OFFLINE',
            }
        )
    return {'success': True, 'online_count': online, 'offline_count': offline, 'records': report}


@router.get('/version-report')
async def agent_version_report(min_supported_version: str = '1.0.0'):
    devices = await device_service.list_devices()
    rows = []
    for d in devices:
        version = d.get('agent_version') or '0.0.0'
        rows.append(
            {
                'device_id': d['id'],
                'device_name': d['device_name'],
                'agent_version': version,
                'outdated': version < min_supported_version,
            }
        )
    return {'success': True, 'min_supported_version': min_supported_version, 'records': rows}
