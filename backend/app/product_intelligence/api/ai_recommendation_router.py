from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.authz import require_permission
from app.core.integration_hooks import emit_audit_event, emit_notification_event
from app.product_intelligence.api._deps import ai_repo
from app.product_intelligence.schemas.ai_recommendation_schema import (
    AiRecommendationResponse,
    AiRecommendationStatusUpdate,
)

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])


@router.get('/ai-suggestions', response_model=list[AiRecommendationResponse], dependencies=[Depends(require_permission('product_intelligence.read'))])
async def ai_suggestions(status: str | None = None):
    rows = await ai_repo.list_all()
    if status:
        rows = [r for r in rows if r['status'] == status]
    return [
        AiRecommendationResponse(
            recommendation_id=r['id'],
            **{
                k: r[k]
                for k in [
                    'module_name',
                    'screen_key',
                    'recommendation_title',
                    'recommendation_text',
                    'evidence_summary',
                    'confidence_score',
                    'severity_level',
                    'status',
                ]
            },
        )
        for r in rows
    ]


@router.put('/ai-suggestions/{item_id}', response_model=AiRecommendationResponse, dependencies=[Depends(require_permission('product_intelligence.write'))])
async def update_ai_suggestion(item_id: int, payload: AiRecommendationStatusUpdate):
    row = await ai_repo.update(item_id, {'status': payload.status})
    if not row:
        raise HTTPException(status_code=404, detail='Recommendation not found')

    emit_audit_event('ai_ux_suggestion_status_updated', {'recommendation_id': item_id, 'status': payload.status})
    emit_notification_event('ai_ux_suggestion_status_updated', {'recommendation_id': item_id, 'status': payload.status})

    return AiRecommendationResponse(
        recommendation_id=row['id'],
        **{
            k: row[k]
            for k in [
                'module_name',
                'screen_key',
                'recommendation_title',
                'recommendation_text',
                'evidence_summary',
                'confidence_score',
                'severity_level',
                'status',
            ]
        },
    )
