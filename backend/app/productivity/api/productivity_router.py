from __future__ import annotations
from fastapi import APIRouter
from app.productivity.api.agent_router import router as agent_router
from app.productivity.api.policy_router import router as policy_router
from app.productivity.api.reports_router import router as reports_router
from app.productivity.api._deps import app_classification_service, device_service, url_classification_service
from app.productivity.schemas.app_classification_schema import AppClassificationResponse, AppClassificationUpsertRequest
from app.productivity.schemas.device_schema import DeviceDeactivateResponse, DeviceRegisterRequest, DeviceResponse
from app.productivity.schemas.url_classification_schema import UrlClassificationResponse, UrlClassificationUpsertRequest

router = APIRouter(prefix='/productivity', tags=['Productivity'])
router.include_router(agent_router)
router.include_router(policy_router)
router.include_router(reports_router)

@router.get('/devices', response_model=list[DeviceResponse])
async def list_devices():
    rows = await device_service.list_devices()
    return [DeviceResponse(device_id=r['id'], device_uuid=r['device_uuid'], device_name=r['device_name'], registration_status=r['registration_status'], user_id=r['employee_user_id']) for r in rows]

@router.post('/devices', response_model=DeviceResponse)
async def create_device(payload: DeviceRegisterRequest):
    row = await device_service.register_device(payload.model_dump())
    return DeviceResponse(device_id=row['id'], device_uuid=row['device_uuid'], device_name=row['device_name'], registration_status=row['registration_status'], user_id=row['employee_user_id'])

@router.put('/devices/{device_id}/deactivate', response_model=DeviceDeactivateResponse)
async def deactivate_device(device_id: int):
    ok = await device_service.deactivate(device_id)
    return DeviceDeactivateResponse(success=ok, device_id=device_id)

@router.get('/app-classification', response_model=list[AppClassificationResponse])
async def list_app_classification():
    rows = await app_classification_service.list_all()
    return [AppClassificationResponse(app_classification_id=r['id'], app_name=r['app_name'], classification_type=r['classification_type']) for r in rows]

@router.post('/app-classification', response_model=AppClassificationResponse)
async def create_app_classification(payload: AppClassificationUpsertRequest):
    row = await app_classification_service.create(payload.model_dump())
    return AppClassificationResponse(app_classification_id=row['id'], app_name=row['app_name'], classification_type=row['classification_type'])

@router.put('/app-classification/{item_id}', response_model=AppClassificationResponse)
async def update_app_classification(item_id: int, payload: AppClassificationUpsertRequest):
    row = await app_classification_service.update(item_id, payload.model_dump())
    row = row or {'id': item_id, 'app_name': payload.app_name, 'classification_type': payload.classification_type}
    return AppClassificationResponse(app_classification_id=row['id'], app_name=row['app_name'], classification_type=row['classification_type'])

@router.get('/url-classification', response_model=list[UrlClassificationResponse])
async def list_url_classification():
    rows = await url_classification_service.list_all()
    return [UrlClassificationResponse(url_classification_id=r['id'], domain_name=r['domain_name'], classification_type=r['classification_type']) for r in rows]

@router.post('/url-classification', response_model=UrlClassificationResponse)
async def create_url_classification(payload: UrlClassificationUpsertRequest):
    row = await url_classification_service.create(payload.model_dump())
    return UrlClassificationResponse(url_classification_id=row['id'], domain_name=row['domain_name'], classification_type=row['classification_type'])

@router.put('/url-classification/{item_id}', response_model=UrlClassificationResponse)
async def update_url_classification(item_id: int, payload: UrlClassificationUpsertRequest):
    row = await url_classification_service.update(item_id, payload.model_dump())
    row = row or {'id': item_id, 'domain_name': payload.domain_name, 'classification_type': payload.classification_type}
    return UrlClassificationResponse(url_classification_id=row['id'], domain_name=row['domain_name'], classification_type=row['classification_type'])


@router.get('/summary')
async def productivity_summary():
    return {
        "summary_kpis": {
            "active_time_minutes": 312,
            "idle_time_minutes": 54,
            "productive_app_time_minutes": 248,
            "non_productive_app_time_minutes": 64,
            "focus_sessions": 9,
            "context_switching_rate": 14,
        },
        "team_comparison": [{"team": "Engineering", "productivity_score": 82}, {"team": "Support", "productivity_score": 76}],
    }


@router.post('/filter')
async def productivity_filter(payload: dict):
    return {
        "filters_applied": payload,
        "rows": [
            {"user_id": 1, "user_name": "Admin", "active_time": 280, "idle_time": 40, "agent_sync_status": "ONLINE"},
            {"user_id": 2, "user_name": "Manager", "active_time": 260, "idle_time": 65, "agent_sync_status": "ONLINE"},
        ],
    }


@router.get('/user-detail/{user_id}')
async def productivity_user_detail(user_id: int):
    return {
        "user_id": user_id,
        "active_vs_idle": {"active": 320, "idle": 55},
        "top_apps": [{"app": "VS Code", "minutes": 140, "category": "PRODUCTIVE"}, {"app": "Browser", "minutes": 100, "category": "MIXED"}],
        "top_urls": [{"url": "github.com", "minutes": 90}, {"url": "jira.example.com", "minutes": 50}],
        "focus_time_analysis": {"focus_sessions": 8, "avg_focus_minutes": 28},
    }


@router.get('/exceptions')
async def productivity_exceptions():
    return {
        "items": [
            {"user_id": 3, "type": "HIGH_IDLE", "detail": "Idle time above threshold", "severity": "MEDIUM"},
            {"user_id": 4, "type": "SYNC_LAG", "detail": "Agent heartbeat delayed", "severity": "HIGH"},
        ]
    }


@router.get('/agent-status')
async def productivity_agent_status():
    return {
        "online_agents": 14,
        "offline_agents": 2,
        "last_sync_summary": [{"user_id": 1, "last_heartbeat": "2026-04-03T08:00:00Z", "status": "ONLINE"}],
    }
