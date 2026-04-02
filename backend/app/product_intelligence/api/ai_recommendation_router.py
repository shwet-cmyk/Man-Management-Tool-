from __future__ import annotations
from fastapi import APIRouter
from app.product_intelligence.api._deps import ai_repo
from app.product_intelligence.schemas.ai_recommendation_schema import AiRecommendationResponse, AiRecommendationStatusUpdate

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])

@router.get('/ai-suggestions', response_model=list[AiRecommendationResponse])
async def ai_suggestions(status: str | None = None):
    rows = await ai_repo.list_all()
    if status:
        rows = [r for r in rows if r['status'] == status]
    return [AiRecommendationResponse(recommendation_id=r['id'], **{k: r[k] for k in ['module_name','screen_key','recommendation_title','recommendation_text','evidence_summary','confidence_score','severity_level','status']}) for r in rows]

@router.put('/ai-suggestions/{item_id}', response_model=AiRecommendationResponse)
async def update_ai_suggestion(item_id: int, payload: AiRecommendationStatusUpdate):
    row = await ai_repo.update(item_id, {'status': payload.status})
    if not row:
        row = await ai_repo.insert({'module_name': 'global', 'screen_key': None, 'recommendation_title': 'Manual review placeholder', 'recommendation_text': 'Created during status update.', 'evidence_summary': None, 'confidence_score': None, 'severity_level': 'LOW', 'status': payload.status})
    return AiRecommendationResponse(recommendation_id=row['id'], **{k: row[k] for k in ['module_name','screen_key','recommendation_title','recommendation_text','evidence_summary','confidence_score','severity_level','status']})
