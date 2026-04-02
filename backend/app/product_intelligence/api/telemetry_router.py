from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.authz import require_permission
from app.core.integration_hooks import emit_audit_event
from app.product_intelligence.api._deps import (
    ai_repo,
    dead_click_repo,
    heatmap_repo,
    rage_click_repo,
    ux_analytics_service,
    ux_error_repo,
    ux_event_repo,
    ux_telemetry_service,
)
from app.product_intelligence.schemas.ux_event_schema import (
    UxEventIngestRequest,
    UxIngestResponse,
)

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])


@router.post('/ux-events', response_model=UxIngestResponse, dependencies=[Depends(require_permission('product_intelligence.write'))])
async def ingest_ux_events(payload: UxEventIngestRequest):
    result = await ux_telemetry_service.ingest(
        event_repo=ux_event_repo,
        dead_repo=dead_click_repo,
        rage_repo=rage_click_repo,
        error_repo=ux_error_repo,
        heatmap_repo=heatmap_repo,
        ai_repo=ai_repo,
        user_id=payload.user_id,
        role_id=payload.role_id,
        session_id=payload.session_id,
        events=[e.model_dump() for e in payload.events],
    )
    emit_audit_event('ux_events_ingested', {'user_id': payload.user_id, 'screen_events': result['ingested_count']})
    return UxIngestResponse(success=True, **result)


@router.get('/overview', dependencies=[Depends(require_permission('product_intelligence.read'))])
async def overview(date_from: str | None = None, date_to: str | None = None):
    return {
        'success': True,
        'overview': await ux_analytics_service.overview(
            event_repo=ux_event_repo,
            dead_repo=dead_click_repo,
            rage_repo=rage_click_repo,
            error_repo=ux_error_repo,
        ),
    }
