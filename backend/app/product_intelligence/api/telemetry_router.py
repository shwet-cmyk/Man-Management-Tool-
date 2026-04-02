from __future__ import annotations
from fastapi import APIRouter
from app.product_intelligence.api._deps import ux_telemetry_service, ux_analytics_service, ux_event_repo, dead_click_repo, rage_click_repo, ux_error_repo, heatmap_repo, ai_repo
from app.product_intelligence.schemas.ux_event_schema import UxEventIngestRequest, UxIngestResponse

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])

@router.post('/ux-events', response_model=UxIngestResponse)
async def ingest_ux_events(payload: UxEventIngestRequest):
    result = await ux_telemetry_service.ingest(event_repo=ux_event_repo, dead_repo=dead_click_repo, rage_repo=rage_click_repo, error_repo=ux_error_repo, heatmap_repo=heatmap_repo, ai_repo=ai_repo, user_id=payload.user_id, role_id=payload.role_id, session_id=payload.session_id, events=[e.model_dump() for e in payload.events])
    return UxIngestResponse(success=True, **result)

@router.get('/overview')
async def overview(date_from: str | None = None, date_to: str | None = None):
    return {'success': True, 'overview': await ux_analytics_service.overview(event_repo=ux_event_repo, dead_repo=dead_click_repo, rage_repo=rage_click_repo, error_repo=ux_error_repo)}
