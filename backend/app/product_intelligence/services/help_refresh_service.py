from __future__ import annotations

class HelpRefreshService:
    async def run_refresh(self, repo, *, release_version: str, affected: list[dict]) -> list[dict]:
        rows = []
        for item in affected:
            rows.append(await repo.insert({'screen_key': item['screen_key'], 'route_path': item.get('route_path'), 'module_name': item['module_name'], 'prior_help_version': item.get('prior_help_version', 'v1'), 'new_help_version': item.get('new_help_version', 'v2'), 'refresh_reason': f"release {release_version}", 'refresh_mode': item.get('refresh_mode', 'AUTO_DRAFT'), 'refresh_status': 'GENERATED', 'triggered_by_release_version': release_version}))
        return rows
