from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.authz import require_permission
from app.product_intelligence.api._deps import feature_change_repo, release_note_repo
from app.product_intelligence.schemas.release_note_schema import ReleaseNoteResponse

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])


@router.get('/release-notes/latest', response_model=list[ReleaseNoteResponse], dependencies=[Depends(require_permission('product_intelligence.read'))])
async def release_notes_latest(module_name: str | None = None):
    rows = sorted(await release_note_repo.list_all(), key=lambda x: x['release_date'], reverse=True)
    if module_name:
        versions = {
            item['release_version']
            for item in await feature_change_repo.list_all()
            if item.get('module_name', '').lower() == module_name.lower()
        }
        rows = [r for r in rows if r['release_version'] in versions]
    rows = rows[:10]
    return [
        ReleaseNoteResponse(
            release_note_id=r['id'],
            **{k: r[k] for k in ['release_version', 'release_title', 'release_summary', 'release_date', 'release_type']},
        )
        for r in rows
    ]


@router.get('/release-notes', response_model=list[ReleaseNoteResponse], dependencies=[Depends(require_permission('product_intelligence.read'))])
async def release_notes(module_name: str | None = None):
    rows = await release_note_repo.list_all()
    if module_name:
        versions = {
            item['release_version']
            for item in await feature_change_repo.list_all()
            if item.get('module_name', '').lower() == module_name.lower()
        }
        rows = [r for r in rows if r['release_version'] in versions]
    return [
        ReleaseNoteResponse(
            release_note_id=r['id'],
            **{k: r[k] for k in ['release_version', 'release_title', 'release_summary', 'release_date', 'release_type']},
        )
        for r in rows
    ]
