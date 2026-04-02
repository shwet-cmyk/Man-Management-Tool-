from __future__ import annotations
from fastapi import APIRouter
from app.product_intelligence.api._deps import feature_change_repo, feature_diff_service, help_refresh_repo, help_refresh_service, release_note_repo, release_notes_service
from app.product_intelligence.schemas.help_refresh_schema import HelpRefreshLogResponse, HelpRefreshRunRequest

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])

@router.get('/help-refresh-log', response_model=list[HelpRefreshLogResponse])
async def help_refresh_log(screen_key: str | None = None):
    rows = await help_refresh_repo.list_all()
    if screen_key:
        rows = [r for r in rows if r['screen_key'] == screen_key]
    return [HelpRefreshLogResponse(help_refresh_id=r['id'], screen_key=r['screen_key'], module_name=r['module_name'], refresh_mode=r['refresh_mode'], refresh_status=r['refresh_status']) for r in rows]

@router.post('/help-refresh/run')
async def help_refresh_run(payload: HelpRefreshRunRequest):
    release = await release_notes_service.create_release_note(release_note_repo, payload.release_version, f'Release {payload.release_version}', 'Auto-generated release summary')
    changes = await feature_diff_service.record_changes(feature_change_repo, release_version=payload.release_version, changes=[{'module_name':'Tasks','screen_key':'task_list','route_path':'/tasks','field_name':'add_task_button_label'},{'module_name':'Approvals','screen_key':'approval_inbox','route_path':'/approvals','field_name':'help_hint_text'}])
    refresh = await help_refresh_service.run_refresh(help_refresh_repo, release_version=payload.release_version, affected=[{'module_name': c['module_name'], 'screen_key': c['screen_key'], 'route_path': c['route_path'], 'refresh_mode': 'AUTO_DRAFT'} for c in changes])
    return {'success': True, 'release_note_id': release['id'], 'feature_changes_count': len(changes), 'help_refresh_count': len(refresh)}

@router.get('/feature-changes')
async def feature_changes(release_version: str):
    rows = [r for r in await feature_change_repo.list_all() if r['release_version'] == release_version]
    return {'success': True, 'records': rows}
