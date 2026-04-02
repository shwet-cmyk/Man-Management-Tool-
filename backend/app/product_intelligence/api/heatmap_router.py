from __future__ import annotations
from fastapi import APIRouter, Query
from app.product_intelligence.api._deps import dead_click_repo, heatmap_repo, rage_click_repo, ux_error_repo

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])

@router.get('/heatmap')
async def heatmap(screen_key: str, heatmap_type: str = Query('CLICK')):
    rows = [h for h in await heatmap_repo.list_all() if h['screen_key'] == screen_key and h['heatmap_type'] == heatmap_type]
    return {'success': True, 'records': rows}

@router.get('/dead-clicks')
async def dead_clicks(screen_key: str, date_from: str | None = None, date_to: str | None = None):
    rows = [d for d in await dead_click_repo.list_all() if d['screen_key'] == screen_key]
    return {'success': True, 'records': rows}

@router.get('/rage-clicks')
async def rage_clicks(screen_key: str):
    rows = [r for r in await rage_click_repo.list_all() if r['screen_key'] == screen_key]
    return {'success': True, 'records': rows}

@router.get('/errors')
async def errors(module_name: str):
    rows = [e for e in await ux_error_repo.list_all() if e['module_name'].lower() == module_name.lower()]
    return {'success': True, 'records': rows}
