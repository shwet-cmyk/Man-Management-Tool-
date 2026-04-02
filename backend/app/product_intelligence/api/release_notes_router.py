from __future__ import annotations
from fastapi import APIRouter
from app.product_intelligence.api._deps import release_note_repo
from app.product_intelligence.schemas.release_note_schema import ReleaseNoteResponse

router = APIRouter(prefix='/product-intelligence', tags=['Product Intelligence'])

@router.get('/release-notes/latest', response_model=list[ReleaseNoteResponse])
async def release_notes_latest():
    rows = sorted(await release_note_repo.list_all(), key=lambda x: x['release_date'], reverse=True)[:10]
    return [ReleaseNoteResponse(release_note_id=r['id'], **{k: r[k] for k in ['release_version','release_title','release_summary','release_date','release_type']}) for r in rows]

@router.get('/release-notes', response_model=list[ReleaseNoteResponse])
async def release_notes(module_name: str | None = None):
    rows = await release_note_repo.list_all()
    return [ReleaseNoteResponse(release_note_id=r['id'], **{k: r[k] for k in ['release_version','release_title','release_summary','release_date','release_type']}) for r in rows]
