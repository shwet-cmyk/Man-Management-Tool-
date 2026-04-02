from __future__ import annotations

class UxAnalyticsService:
    async def overview(self, *, event_repo, dead_repo, rage_repo, error_repo) -> dict:
        events = await event_repo.list_all()
        dead = await dead_repo.list_all()
        rage = await rage_repo.list_all()
        errors = await error_repo.list_all()
        return {
            'total_events': len(events),
            'dead_clicks': len(dead),
            'rage_clicks': len(rage),
            'error_events': len(errors),
            'unique_screens': len(set(e['screen_key'] for e in events)) if events else 0,
        }
