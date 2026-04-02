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
