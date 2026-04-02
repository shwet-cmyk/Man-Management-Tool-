from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.authz import require_permission
from app.core.integration_hooks import emit_audit_event, emit_notification_event
from app.product_intelligence.api._deps import (
    feature_change_repo,
    feature_diff_service,
    help_refresh_repo,
    help_refresh_service,
    release_note_repo,
    release_notes_service,
)
from app.product_intelligence.schemas.help_refresh_schema import (
    HelpRefreshLogResponse,
    HelpRefreshRunRequest,
)

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])


@router.get('/help-refresh-log', response_model=list[HelpRefreshLogResponse], dependencies=[Depends(require_permission('product_intelligence.read'))])
async def help_refresh_log(screen_key: str | None = None):
    rows = await help_refresh_repo.list_all()
    if screen_key:
        rows = [r for r in rows if r['screen_key'] == screen_key]
    return [
        HelpRefreshLogResponse(
            help_refresh_id=r['id'],
            screen_key=r['screen_key'],
            module_name=r['module_name'],
            refresh_mode=r['refresh_mode'],
            refresh_status=r['refresh_status'],
        )
        for r in rows
    ]


@router.post('/help-refresh/run', dependencies=[Depends(require_permission('product_intelligence.write'))])
async def help_refresh_run(payload: HelpRefreshRunRequest):
    if not payload.changes:
        raise HTTPException(status_code=400, detail='At least one change item is required for help refresh run')

    release = await release_notes_service.create_release_note(
        release_note_repo,
        payload.release_version,
        payload.release_title or f'Release {payload.release_version}',
        payload.release_summary or 'Auto-generated release summary',
    )

    changes = await feature_diff_service.record_changes(
        feature_change_repo,
        release_version=payload.release_version,
        changes=[c.model_dump() for c in payload.changes],
    )

    refresh = await help_refresh_service.run_refresh(
        help_refresh_repo,
        release_version=payload.release_version,
        affected=[
            {
                'module_name': c['module_name'],
                'screen_key': c['screen_key'],
                'route_path': c.get('route_path'),
                'refresh_mode': 'AUTO_DRAFT',
            }
            for c in changes
        ],
    )

    emit_audit_event('help_refresh_run', {'release_version': payload.release_version, 'feature_changes_count': len(changes)})
    emit_notification_event('help_refresh_run_completed', {'release_version': payload.release_version, 'help_refresh_count': len(refresh)})

    return {
        'success': True,
        'release_note_id': release['id'],
        'feature_changes_count': len(changes),
        'help_refresh_count': len(refresh),
    }


@router.get('/feature-changes', dependencies=[Depends(require_permission('product_intelligence.read'))])
async def feature_changes(release_version: str):
    rows = [
        r
        for r in await feature_change_repo.list_all()
        if r['release_version'] == release_version
    ]
    return {'success': True, 'records': rows}
