from __future__ import annotations
from app.product_intelligence.utils.release_diff_parser import classify_change

class FeatureDiffService:
    async def record_changes(self, repo, *, release_version: str, changes: list[dict]) -> list[dict]:
        rows = []
        for c in changes:
            rows.append(await repo.insert({
                'release_version': release_version,
                'module_name': c.get('module_name', 'Unknown'),
                'screen_key': c.get('screen_key'),
                'route_path': c.get('route_path'),
                'component_name': c.get('component_name'),
                'field_name': c.get('field_name'),
                'old_value': c.get('old_value'),
                'new_value': c.get('new_value'),
                'change_category': c.get('change_category') or classify_change(c.get('field_name')),
            }))
        return rows
