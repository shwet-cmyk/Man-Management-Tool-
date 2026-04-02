from __future__ import annotations
from datetime import date

from app.product_intelligence.services.ai_ux_recommendation_service import AiUxRecommendationService
from app.product_intelligence.services.friction_detection_service import FrictionDetectionService
from app.product_intelligence.services.heatmap_service import HeatmapService

class UxTelemetryService:
    def __init__(self, friction: FrictionDetectionService, heatmap: HeatmapService, ai_service: AiUxRecommendationService) -> None:
        self.friction = friction
        self.heatmap = heatmap
        self.ai_service = ai_service

    async def ingest(self, *, event_repo, dead_repo, rage_repo, error_repo, heatmap_repo, ai_repo, user_id: int, role_id: int | None, session_id: str, events: list[dict]) -> dict:
        normalized = []
        for e in events:
            row = {
                'user_id': user_id,
                'role_id': role_id,
                'company_id': 1,
                'branch_id': None,
                'department_id': None,
                'session_id': session_id,
                **e,
                'metadata_json': str(e.get('metadata') or {}),
            }
            normalized.append(row)
            await event_repo.insert(row)
            if row['event_type'] in {'API_ERROR', 'FORM_VALIDATION_ERROR'}:
                await error_repo.insert({'user_id': user_id, 'route_path': row['route_path'], 'screen_key': row['screen_key'], 'module_name': row['module_name'], 'error_type': row['event_type'], 'error_code': None, 'error_message': row.get('element_label'), 'api_path': row.get('route_path'), 'event_timestamp': row['event_timestamp'], 'metadata_json': row['metadata_json']})

        dead_clicks, rage_clicks = self.friction.detect(normalized)
        for d in dead_clicks:
            await dead_repo.insert({'user_id': user_id, **d, 'metadata_json': '{}'})
        for r in rage_clicks:
            await rage_repo.insert({'user_id': user_id, **r, 'metadata_json': '{}'})

        for h in self.heatmap.aggregate(normalized, 'CLICK'):
            await heatmap_repo.insert({**h, 'aggregate_date': date.today(), 'metadata_json': '{}'})

        errors = await error_repo.list_all()
        recs = self.ai_service.generate(dead_clicks=dead_clicks, rage_clicks=rage_clicks, error_events=errors)
        for r in recs:
            await ai_repo.insert(r)

        return {'ingested_count': len(normalized), 'dead_click_count': len(dead_clicks), 'rage_click_count': len(rage_clicks)}
