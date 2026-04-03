from __future__ import annotations
from datetime import datetime, UTC

class ReleaseNotesService:
    async def create_release_note(self, repo, release_version: str, title: str, summary: str, release_type: str = 'IMPROVEMENT') -> dict:
        return await repo.insert({'release_version': release_version, 'release_title': title, 'release_summary': summary, 'release_date': datetime.now(UTC), 'release_type': release_type, 'visibility_scope': 'ALL', 'is_published': True, 'published_at': datetime.now(UTC)})
